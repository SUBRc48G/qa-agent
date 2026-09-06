import os
import re
import json
from collections import Counter
from dotenv import load_dotenv
from datetime import datetime
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from pypdf import PdfReader
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from crewai import Agent, Task, Crew, LLM
from rag_store import retrieve_context

# ---------------- UTILITIES ----------------

def safe(val):
    if isinstance(val, list):
        return "\n".join(safe(x) for x in val)
    if isinstance(val, dict):
        return json.dumps(val)
    if val is None:
        return ""
    return str(val)


def extract_json(text):
    """Robust JSON extractor"""
    if not text:
        return None

    text = str(text).strip()

    # direct parse
    try:
        return json.loads(text)
    except:
        pass

    # try markdown code blocks (prefer last block)
    code_blocks = re.findall(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    for block in reversed(code_blocks):
        try:
            return json.loads(block.strip())
        except:
            pass

    # if text starts with bracket, validate it's properly formed
    if text and text[0] in '[{':
        bracket_type = '[' if text[0] == '[' else '{'
        close_bracket = ']' if bracket_type == '[' else '}'
        depth = 0

        for end_idx in range(len(text)):
            if text[end_idx] == bracket_type:
                depth += 1
            elif text[end_idx] == close_bracket:
                depth -= 1
                if depth == 0:
                    json_str = text[:end_idx+1]
                    # check remaining content after closing bracket
                    remaining = text[end_idx+1:].strip()

                    # if no remaining content, parse the top-level structure
                    if not remaining:
                        try:
                            return json.loads(json_str)
                        except:
                            return None

                    # if remaining has structural garbage (closing bracket), reject
                    if remaining and remaining[0] == '}':
                        return None

                    # if remaining has any content (prose or other brackets),
                    # use regex to find all JSON and return the last valid one
                    break

        # reached end without closing bracket = truncated JSON
        if text.count(bracket_type) > text.count(close_bracket):
            return None

    # try greedy regex first (handles cases with text between same-type brackets)
    matches = re.findall(r"\{.*\}|\[.*\]", text, re.DOTALL)

    # try to parse each match in reverse order (prefer the last/rightmost valid JSON)
    for m in reversed(matches):
        try:
            return json.loads(m)
        except:
            pass

    # if greedy regex produced exactly one match that failed to parse,
    # check if it's the "known limitation" (objects with text between, not just primitives)
    if len(matches) == 1:
        m = matches[0]
        # Check if it looks like multiple objects with text between them
        # (pattern: }...text...{  with the text containing colons/quotes suggesting JSON keys)
        if '}\n' in m and '{' in m and re.search(r'\}\s*\w+.*\{', m):
            # further check: if it contains ":" it's likely JSON with keys, indicating known limitation
            if ':' in m:
                return None

    # if greedy regex found no valid JSON, try bracket-matching for embedded structures
    # but avoid matching nested structures (only match top-level structures in the text)
    candidates = []
    i = 0

    while i < len(text):
        char = text[i]
        if char == '{':
            depth = 0
            for end_idx in range(i, len(text)):
                if text[end_idx] == '{':
                    depth += 1
                elif text[end_idx] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            parsed = json.loads(text[i:end_idx+1])
                            candidates.append((i, parsed))
                        except:
                            pass
                        i = end_idx + 1
                        break
            else:
                i += 1
        elif char == '[':
            depth = 0
            for end_idx in range(i, len(text)):
                if text[end_idx] == '[':
                    depth += 1
                elif text[end_idx] == ']':
                    depth -= 1
                    if depth == 0:
                        try:
                            parsed = json.loads(text[i:end_idx+1])
                            candidates.append((i, parsed))
                        except:
                            pass
                        i = end_idx + 1
                        break
            else:
                i += 1
        else:
            i += 1

    # return the last valid JSON found (rightmost in the text)
    if candidates:
        return candidates[-1][1]

    return None


def _json_array_guardrail(task_output):
    """Crew guardrail: forces a retry if the task didn't return a parseable JSON array/object."""
    data = extract_json(task_output.raw)
    if data is None:
        return (False, "Your last response was not valid JSON. Return ONLY a valid JSON array, "
                        "with no markdown fences and no explanation before or after it.")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return (False, "Return a JSON array of objects, not a single value.")
    return (True, task_output.raw)


def _json_object_guardrail(task_output):
    """Crew guardrail: forces a retry if the task didn't return a parseable JSON object."""
    data = extract_json(task_output.raw)
    if not isinstance(data, dict):
        return (False, "Your last response was not a valid JSON object. Return ONLY a single valid "
                        "JSON object, with no markdown fences and no explanation before or after it.")
    return (True, task_output.raw)


def normalize_req(r):
    return {
        "req_id": safe(r.get("req_id")),
        "requirement": safe(r.get("requirement")),
        "category": safe(r.get("category")),
        "priority": safe(r.get("priority")),
    }


def format_steps(steps):
    """Render steps as a clean, numbered, newline-separated list for Excel display."""
    if isinstance(steps, list):
        lines = []
        for i, s in enumerate(steps, 1):
            s = str(s).strip()
            if re.match(r"^\d+[\.\)]", s):
                lines.append(s)
            else:
                lines.append(f"{i}. {s}")
        return "\n".join(lines)
    return safe(steps)


def normalize_tc(tc, automation_lookup=None):
    tc_id = safe(tc.get("id"))
    automatable = (automation_lookup or {}).get(tc_id, {}).get("automatable", "")
    return {
        "id": tc_id,
        "req_id": safe(tc.get("req_id")),
        "scenario": safe(tc.get("scenario")),
        "type": safe(tc.get("type")),
        "steps": format_steps(tc.get("steps")),
        "expected_result": safe(tc.get("expected_result")),
        "priority": safe(tc.get("priority")),
        "automatable": automatable,
    }


def normalize_automation(a, scenario_lookup):
    tc_id = safe(a.get("id"))
    return {
        "id": tc_id,
        "scenario": scenario_lookup.get(tc_id, ""),
        "automatable": safe(a.get("automatable")),
        "recommended_tool": safe(a.get("recommended_tool")),
        "reason": safe(a.get("reason")),
    }


def style_sheet(ws, col_widths, wrap_cols=None):
    """Set column widths, wrap long text, top-align cells, and grow row height to fit content."""
    for idx, width in enumerate(col_widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = width

    wrap_cols = set(wrap_cols) if wrap_cols is not None else set(range(1, len(col_widths) + 1))

    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, max_col=len(col_widths)):
        max_lines = 1
        for cell in row:
            if cell.column in wrap_cols:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            if isinstance(cell.value, str) and "\n" in cell.value:
                max_lines = max(max_lines, cell.value.count("\n") + 1)
        ws.row_dimensions[row[0].row].height = max(15, min(15 * max_lines, 409))

    ws.freeze_panes = "A2"


def load_requirements(file_path):
    """Extract requirement text from an uploaded .txt, .pdf, .docx or .xlsx file."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".pdf":
        reader = PdfReader(file_path)
        return "".join(page.extract_text() or "" for page in reader.pages)

    elif ext == ".docx":
        document = Document(file_path)
        parts = [p.text for p in document.paragraphs if p.text.strip()]

        for table in document.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))

        return "\n".join(parts)

    elif ext == ".xlsx":
        wb = load_workbook(file_path, data_only=True)
        parts = []

        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
                if cells:
                    parts.append(" | ".join(cells))

        return "\n".join(parts)

    else:
        raise ValueError("Unsupported file format. Supported: .txt, .pdf, .docx, .xlsx")


def load_requirements_auto():
    for file in ["requirements.pdf", "qa_requirements.txt"]:
        if os.path.exists(file):
            return load_requirements(file)
    raise FileNotFoundError("No requirement file found")


# ---------------- INIT ----------------

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OPENAI_API_KEY")

model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
default_testcases_per_day = int(os.getenv("TEST_CASES_PER_DAY", 20))

llm = LLM(model=model_name)


# ---------------- AGENTS ----------------
# Agents hold no per-run state, so they are safe to create once and reuse across pipeline runs.

analyst = Agent(role="Analyst", goal="Break requirements down into a structured, itemized list", backstory="QA expert", llm=llm, verbose=True)

qa_engineer = Agent(role="QA Engineer", goal="Generate the best possible, highest-coverage test cases", backstory="QA expert", llm=llm, verbose=True)

reviewer = Agent(role="Reviewer", goal="Review test cases", backstory="Senior QA", llm=llm, verbose=True)

fixer = Agent(role="Fixer", goal="Fix test cases", backstory="Senior QA", llm=llm, verbose=True)

automation_analyst = Agent(
    role="Automation Analyst",
    goal="Assess automation feasibility for each test case and recommend the right automation tool",
    backstory="Senior SDET with deep expertise across UI, API, mobile and performance automation frameworks",
    llm=llm,
    verbose=True
)

estimator = Agent(role="Estimator", goal="Estimate effort", backstory="QA lead", llm=llm, verbose=True)

strategy_writer = Agent(
    role="QA Lead",
    goal="Write clear, professional test strategy narrative tailored to the project",
    backstory="Senior QA Lead who has authored test strategy documents for many enterprise projects",
    llm=llm,
    verbose=True
)


# ---------------- PIPELINE ----------------

STAGE_LABELS = {
    "analyze": "✅ Requirements analyzed",
    "generate": "✅ Test cases generated",
    "review": "✅ Test cases reviewed",
    "fix": "✅ Test cases fixed",
    "automation": "✅ Automation feasibility assessed",
    "estimate": "✅ Effort estimated",
}


def run_pipeline(requirements, testcases_per_day=None, output_dir=".", progress_callback=None):
    """
    Run the full QA crew (analyze -> generate -> review -> fix -> automation -> estimate)
    against the given requirements text and write all Excel reports into output_dir.

    progress_callback, if given, is called with a short human-readable string as each
    stage completes (e.g. "✅ Test cases generated"), so a UI can show live progress.

    Returns a dict describing what was produced, so a caller (CLI or UI) can display
    a summary and offer the generated files for download. Any stage whose output could
    not be parsed as valid JSON (even after guardrail retries) is listed under "warnings"
    instead of failing the whole run silently.
    """
    testcases_per_day = testcases_per_day or default_testcases_per_day
    os.makedirs(output_dir, exist_ok=True)

    def notify(message):
        if progress_callback:
            progress_callback(message)

    # ---------------- TASKS (fresh per run, since they embed this run's requirements text) ----------------

    task1 = Task(
        description=f"""
Analyze the requirements below and break them down into a structured, itemized list.

RULES:
- Output ONLY a valid JSON array
- No markdown
- No explanation
- Split the requirements into distinct, atomic requirement items
- Each item must have:
  req_id, requirement, category, priority
  - req_id: e.g. "REQ_1", "REQ_2"
  - category: "Functional" or "Non-Functional"
  - priority: "High", "Medium", or "Low"

FORMAT EXAMPLE:
[
  {{
    "req_id": "REQ_1",
    "requirement": "User must be able to log in using email and password",
    "category": "Functional",
    "priority": "High"
  }}
]

Requirements:
{requirements}
""",
        expected_output="JSON array of requirement items",
        agent=analyst,
        name="analyze",
        guardrail=_json_array_guardrail,
    )

    task2 = Task(
        description=f"""
Using the itemized requirements from the analysis above, generate the BEST possible set of test cases
that gives maximum coverage of the requirements.

RULES:
- Output ONLY valid JSON array
- No markdown
- No explanation
- For every requirement, evaluate it against ALL of the test types below. Do NOT skip
  a type just because the requirement text doesn't explicitly mention it — infer
  applicability from what the requirement DOES, using the trigger patterns given.
  Only skip a type if none of its triggers apply at all.

  MANDATORY TYPES (apply the trigger test below to every requirement; if it matches,
  you MUST write that test case):
  - Positive (Functional): always applies — the requirement works with valid input/flow
  - Negative: always applies — invalid input, missing/incorrect data, disallowed action
  - Edge/Boundary: always applies — min/max values, empty/null, zero results, very large input
  - Security: applies whenever the requirement mentions a user role, permission, scope,
    license, credentials, or restricted action -> write a test that tries to bypass or
    exceed that restriction (e.g. a Read-only role attempting a write/delete action,
    or an action attempted without the required license)
  - Performance/Load: applies whenever the requirement involves listing, searching,
    filtering, retrieving, deleting, or otherwise processing multiple/bulk records ->
    write a test verifying acceptable response time when the data set is very large
    (e.g. thousands of records) or under concurrent requests
  - Data Validation: applies whenever the requirement involves structured data fields
    (IDs, names, dates, formats) -> write a test checking format/type/length consistency

  CONDITIONAL TYPES (include only if the requirement genuinely involves this):
  - Usability/UX: only if the requirement describes a user-facing UI/workflow
  - Compatibility: only if multiple browsers, devices, OS, or API versions are implied
  - Integration: only if the requirement explicitly involves another module/system/API
  - Regression: only if the requirement modifies/replaces existing behavior
  - Accessibility: only if the requirement describes a user-facing UI screen

- Before finalizing, double check: does the final list contain at least one Security
  test and at least one Performance test for every requirement that has a role/permission
  aspect or a list/search/bulk aspect respectively? If not, add them.
- Prioritize high-value, realistic scenarios; do not pad with irrelevant conditional types
- Every applicable type from the MANDATORY list MUST be its own separate test case object.
  Never combine two different types (e.g. a Positive check and a Security check) into a
  single test case just to keep the list short — each gets its own id, scenario and steps.
- "Do not create duplicate or redundant test cases" means do not repeat the exact same
  scenario twice — it does NOT mean skipping a mandatory type to save space
- Every test case must reference the req_id of the requirement it covers
- Each test case must have:
  id, req_id, scenario, type, steps, expected_result, priority
  - type: one of "Positive", "Negative", "Edge", "Security", "Usability",
    "Performance", "Compatibility", "Integration", "Data Validation",
    "Regression", "Accessibility"
  - steps: a JSON array of short, discrete step strings (one action per element,
    NOT a single paragraph), e.g. ["Open the login page", "Enter valid credentials",
    "Click Login"]. Do not number the steps yourself, that is added afterwards.

FORMAT EXAMPLE:
[
  {{
    "id": "TC_1",
    "req_id": "REQ_1",
    "scenario": "Login test",
    "type": "Positive",
    "steps": ["Open the login page", "Enter valid credentials", "Click Login"],
    "expected_result": "User logs in",
    "priority": "High"
  }}
]

Requirements:
{requirements}
""",
        expected_output="JSON array only",
        agent=qa_engineer,
        context=[task1],
        name="generate",
        guardrail=_json_array_guardrail,
    )

    task3 = Task(
        description="""
Review test cases and return ONLY JSON:

[
  {"id":"TC_1","review_comment":"..."}
]
""",
        expected_output="JSON only",
        agent=reviewer,
        context=[task2],
        name="review",
        guardrail=_json_array_guardrail,
    )

    task4 = Task(
        description="""
Fix the test cases based on the review comments.

RULES:
- Output ONLY valid JSON array
- No markdown, no explanation
- The output must contain EVERY test case id from the original list. Do not drop, merge,
  or silently remove a test case — even ones with no review comment must be carried
  through unchanged.
- Only remove a test case if its review comment explicitly says it is invalid, unsafe,
  or an exact duplicate of another id
- For every other test case, apply the fix described in its review comment (if any) and
  keep its id, req_id and type

Return ONLY final JSON array.
""",
        expected_output="Final JSON only",
        agent=fixer,
        context=[task2, task3],
        name="fix",
        guardrail=_json_array_guardrail,
    )

    task5 = Task(
        description="""
Analyze the FINAL test cases and determine automation feasibility for each one.

RULES:
- Output ONLY valid JSON array
- No markdown
- No explanation
- For every test case decide:
  - automatable: "Yes" or "No"
  - recommended_tool: the most suitable tool/framework for that test case, e.g.
    Selenium/Playwright/Cypress for Web UI, Appium for Mobile, Postman/RestAssured/pytest+requests
    for API, JMeter/k6 for Performance, or "Manual" if it cannot/should not be automated
    (e.g. exploratory, usability, one-off, or requires human judgement)
  - reason: one short sentence justifying the decision

FORMAT EXAMPLE:
[
  {"id":"TC_1","automatable":"Yes","recommended_tool":"Selenium","reason":"Simple, stable UI login flow"}
]
""",
        expected_output="JSON array only",
        agent=automation_analyst,
        context=[task4],
        name="automation",
        guardrail=_json_array_guardrail,
    )

    task6 = Task(
        description=f"""
Estimate effort.

Return JSON:
{{
 "total_test_cases": number,
 "test_cases_per_day": {testcases_per_day},
 "estimated_days": number
}}
""",
        expected_output="Estimation JSON",
        agent=estimator,
        context=[task4],
        name="estimate",
        guardrail=_json_object_guardrail,
    )

    # ---------------- CREW ----------------

    def _on_task_complete(task_output):
        notify(STAGE_LABELS.get(task_output.name, f"✅ Completed: {task_output.name}"))

    crew = Crew(
        agents=[analyst, qa_engineer, reviewer, fixer, automation_analyst, estimator],
        tasks=[task1, task2, task3, task4, task5, task6],
        verbose=True,
        memory=False,
        task_callback=_on_task_complete,
    )

    print("🚀 Running Crew...")
    notify("🚀 Starting QA crew...")
    crew_error = None
    try:
        crew.kickoff()
        print("✅ Crew completed")
    except Exception as e:
        # A task can exhaust its guardrail retries (bad JSON from the LLM even after
        # several attempts) and raise instead of just returning bad output. Degrade
        # gracefully: keep whatever tasks did complete and surface this as a warning
        # rather than crashing the whole run.
        crew_error = str(e)
        print(f"❌ Crew execution failed: {crew_error}")
        notify(f"❌ Crew execution stopped early: {crew_error}")

    # ---------------- EXTRACT JSON ----------------

    requirement_items = extract_json(task1.output)
    test_cases = extract_json(task2.output)
    reviews = extract_json(task3.output)
    updated_cases = extract_json(task4.output)
    automation_results = extract_json(task5.output)
    estimation = extract_json(task6.output)

    if isinstance(requirement_items, dict):
        requirement_items = [requirement_items]
    if isinstance(test_cases, dict):
        test_cases = [test_cases]
    if isinstance(reviews, dict):
        reviews = [reviews]
    if isinstance(updated_cases, dict):
        updated_cases = [updated_cases]
    if isinstance(automation_results, dict):
        automation_results = [automation_results]

    print(f"🔢 Stage counts — requirements: {len(requirement_items or [])}, "
          f"generated test cases: {len(test_cases or [])}, "
          f"reviews: {len(reviews or [])}, "
          f"final test cases: {len(updated_cases or [])}, "
          f"automation results: {len(automation_results or [])}")

    warnings = []
    if crew_error:
        warnings.append(f"The QA crew stopped early: {crew_error}")
    if not requirement_items:
        warnings.append("Could not extract structured requirements from the analysis step — "
                         "the requirements report was not generated.")
    if not test_cases:
        warnings.append("Could not extract generated test cases — the draft test cases report was not generated.")
    if not updated_cases:
        warnings.append("Could not extract final test cases after review/fix — "
                         "the final test cases report was not generated.")
    if not automation_results:
        warnings.append("Could not extract automation feasibility results — "
                         "the automation feasibility report was not generated.")
    if not estimation:
        warnings.append("Could not extract effort estimation — the estimation report was not generated.")

    for w in warnings:
        print(f"⚠️ {w}")
        notify(f"⚠️ {w}")

    notify("📊 Writing Excel reports...")

    automation_lookup = {}
    if automation_results:
        for a in automation_results:
            automation_lookup[safe(a.get("id"))] = {
                "automatable": safe(a.get("automatable")),
                "recommended_tool": safe(a.get("recommended_tool")),
            }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files = {}

    # ---------------- REQUIREMENTS EXCEL ----------------

    wb0 = Workbook()
    ws0 = wb0.active
    ws0.title = "Requirements"
    ws0.append(["Req ID", "Requirement", "Category", "Priority"])

    if requirement_items:
        for r in requirement_items:
            ws0.append(list(normalize_req(r).values()))

        style_sheet(ws0, col_widths=[10, 60, 16, 10])
        path = os.path.join(output_dir, "requirements_analysis.xlsx")
        wb0.save(path)
        files["requirements"] = path
        print(f"📊 {len(requirement_items)} requirement(s) saved to {path}")
    else:
        print("❌ No requirements extracted")

    # ---------------- TEST CASES EXCEL ----------------

    wb1 = Workbook()
    ws1 = wb1.active
    ws1.title = "Test Cases"
    ws1.append(["ID", "Req ID", "Scenario", "Type", "Steps", "Expected Result", "Priority", "Automatable"])

    if test_cases:
        for tc in test_cases:
            ws1.append(list(normalize_tc(tc, automation_lookup).values()))

        style_sheet(ws1, col_widths=[10, 10, 30, 14, 55, 35, 10, 14])
        path = os.path.join(output_dir, "test_cases.xlsx")
        wb1.save(path)
        files["test_cases"] = path
        print("📊 Test cases saved")
    else:
        print("❌ No test cases found")

    # ---------------- REVIEW EXCEL ----------------

    wb2 = Workbook()
    ws2 = wb2.active
    ws2.title = "Review"
    ws2.append(["ID", "Comment"])

    if reviews:
        for r in reviews:
            ws2.append([safe(r.get("id")), safe(r.get("review_comment"))])

        style_sheet(ws2, col_widths=[10, 80])
        path = os.path.join(output_dir, "review_comments.xlsx")
        wb2.save(path)
        files["review"] = path
        print("📊 Review saved")

    # ---------------- FINAL TEST CASES EXCEL ----------------

    wb3 = Workbook()
    ws3 = wb3.active
    ws3.title = "Final Cases"
    ws3.append(["ID", "Req ID", "Scenario", "Type", "Steps", "Expected Result", "Priority", "Automatable"])

    scenario_lookup = {}
    final_cases_normalized = []

    if updated_cases:
        for tc in updated_cases:
            norm = normalize_tc(tc, automation_lookup)
            ws3.append(list(norm.values()))
            scenario_lookup[norm["id"]] = norm["scenario"]
            final_cases_normalized.append(norm)

        style_sheet(ws3, col_widths=[10, 10, 30, 14, 55, 35, 10, 14])
        path = os.path.join(output_dir, f"final_{timestamp}.xlsx")
        wb3.save(path)
        files["final"] = path
        print("📊 Final test cases saved")

    # ---------------- AUTOMATION FEASIBILITY EXCEL ----------------

    automation_summary = None

    if automation_results:
        wb5 = Workbook()
        ws5 = wb5.active
        ws5.title = "Automation Feasibility"
        ws5.append(["ID", "Scenario", "Automatable", "Recommended Tool", "Reason"])

        normalized_automation = [normalize_automation(a, scenario_lookup) for a in automation_results]

        for a in normalized_automation:
            ws5.append(list(a.values()))

        style_sheet(ws5, col_widths=[10, 30, 14, 20, 45])

        total_cases = len(normalized_automation)
        automatable_count = sum(1 for a in normalized_automation if a["automatable"].strip().lower() == "yes")
        manual_count = total_cases - automatable_count
        automation_pct = round((automatable_count / total_cases) * 100, 1) if total_cases else 0

        tool_counts = Counter(
            a["recommended_tool"] for a in normalized_automation if a["automatable"].strip().lower() == "yes"
        )

        ws6 = wb5.create_sheet("Summary")
        ws6.append(["Metric", "Value"])
        ws6.append(["Total Test Cases", total_cases])
        ws6.append(["Automatable", automatable_count])
        ws6.append(["Manual Only", manual_count])
        ws6.append(["Automation Coverage %", automation_pct])
        ws6.append([])
        ws6.append(["Recommended Tool", "Test Case Count"])
        for tool, count in tool_counts.most_common():
            ws6.append([tool, count])

        style_sheet(ws6, col_widths=[25, 20])
        path = os.path.join(output_dir, f"automation_feasibility_{timestamp}.xlsx")
        wb5.save(path)
        files["automation"] = path

        automation_summary = {
            "total": total_cases,
            "automatable": automatable_count,
            "manual": manual_count,
            "coverage_pct": automation_pct,
            "tool_counts": dict(tool_counts),
        }

        print(f"📊 Automation feasibility saved: {automatable_count}/{total_cases} ({automation_pct}%) test cases can be automated")
        for tool, count in tool_counts.most_common():
            print(f"   - {tool}: {count} test case(s)")
    else:
        print("❌ No automation feasibility results found")

    # ---------------- ESTIMATION EXCEL ----------------

    if estimation:
        wb4 = Workbook()
        ws4 = wb4.active
        ws4.title = "Estimation"
        ws4.append(["Total TC", "Per Day", "Days"])
        ws4.append([
            estimation.get("total_test_cases", 0),
            estimation.get("test_cases_per_day", testcases_per_day),
            estimation.get("estimated_days", 0)
        ])

        style_sheet(ws4, col_widths=[15, 12, 10])
        path = os.path.join(output_dir, f"estimation_{timestamp}.xlsx")
        wb4.save(path)
        files["estimation"] = path
        print("📊 Estimation saved")

    notify("🎉 Pipeline completed")
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY")

    return {
        "timestamp": timestamp,
        "output_dir": output_dir,
        "files": files,
        "warnings": warnings,
        "counts": {
            "requirements": len(requirement_items or []),
            "generated_test_cases": len(test_cases or []),
            "reviews": len(reviews or []),
            "final_test_cases": len(updated_cases or []),
        },
        "automation_summary": automation_summary,
        "estimation": estimation,
        "data": {
            "requirements": [normalize_req(r) for r in requirement_items] if requirement_items else [],
            "final_test_cases": final_cases_normalized,
        },
    }


# ---------------- TEST STRATEGY DOCUMENT ----------------

DEFAULT_ENTRY_CRITERIA = [
    "Requirements are finalized and reviewed",
    "Test environment and test data are available",
    "Test cases are reviewed and approved",
]

DEFAULT_EXIT_CRITERIA = [
    "All planned test cases have been executed",
    "No open Critical/High severity defects remain",
    "Test summary report is reviewed and approved",
]

DEFAULT_RISKS = [
    {"risk": "Ambiguous or changing requirements", "mitigation": "Maintain a requirement traceability matrix and re-baseline test cases on change"},
    {"risk": "Test environment instability", "mitigation": "Set up a dedicated, monitored test environment ahead of execution"},
]

ROLES_AND_RESPONSIBILITIES = [
    ("QA Lead", "Owns the test strategy, allocates resources, reviews plans/reports, and tracks quality metrics."),
    ("Test Engineer", "Designs, executes and maintains test cases, and logs/retests defects."),
    ("Automation Engineer", "Builds and maintains automation scripts for automatable test cases and integrates them into CI/CD."),
    ("Developer", "Fixes defects, supports root cause analysis, and performs unit/component testing."),
    ("Product Owner", "Clarifies requirements, prioritizes defects, and signs off on releases."),
]

DELIVERABLES = [
    "Test Strategy Document",
    "Test Plan",
    "Test Cases (draft and final, with automation feasibility)",
    "Automation Scripts",
    "Defect Reports",
    "Test Summary Report",
    "Requirement Traceability Matrix",
]

KPIS = [
    "Test Coverage % — proportion of requirements mapped to at least one executed test case",
    "Defect Density — number of defects per requirement/module",
    "Pass/Fail Rate — percentage of executed test cases passing vs failing",
    "Escaped Defects — defects found in production after release",
]

REPORTING_CADENCE = [
    "Daily test execution status shared during stand-up",
    "Weekly test summary report circulated to stakeholders",
    "Final Test Closure Report published at the end of the test cycle",
]


def _add_table(doc, headers, rows, style="Light List Accent 1"):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = style
    for cell, header in zip(table.rows[0].cells, headers):
        cell.text = header
        cell.paragraphs[0].runs[0].bold = True
    for row_data in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row_data):
            cell.text = str(value)
    return table


def _add_bullets(doc, items):
    for item in items:
        doc.add_paragraph(str(item), style="List Bullet")


def generate_test_strategy(requirement_items, final_test_cases, automation_summary, estimation, output_dir="."):
    """
    Build a Test Strategy .docx from already-computed pipeline data (requirements, final
    test cases, automation feasibility, estimation), with an LLM writing the narrative
    sections (objectives, approach, entry/exit criteria, risks) grounded in that data.

    Returns the path to the generated .docx.
    """
    os.makedirs(output_dir, exist_ok=True)

    type_counts = Counter(tc.get("type") for tc in final_test_cases if tc.get("type"))

    traceability = {}
    for tc in final_test_cases:
        traceability.setdefault(tc.get("req_id") or "Unmapped", []).append(tc.get("id", ""))

    req_summary = "\n".join(f'{r["req_id"]}: {r["requirement"]}' for r in requirement_items) or "No requirements available"
    type_summary = ", ".join(f"{t}: {c}" for t, c in type_counts.items()) or "No test cases available"

    if automation_summary:
        automation_line = (
            f'{automation_summary["automatable"]}/{automation_summary["total"]} '
            f'({automation_summary["coverage_pct"]}%) test cases automatable. '
            f'Tools: {", ".join(automation_summary["tool_counts"].keys()) or "n/a"}'
        )
    else:
        automation_line = "Automation feasibility not available"

    if estimation:
        estimation_line = (
            f'{estimation.get("total_test_cases", "n/a")} total test cases, '
            f'{estimation.get("test_cases_per_day", "n/a")} per day, '
            f'{estimation.get("estimated_days", "n/a")} estimated days'
        )
    else:
        estimation_line = "Estimation not available"

    task = Task(
        description=f"""
Write the narrative content for a Test Strategy document for this project. Base it on the
actual project data below — do not invent unrelated details.

Project requirements:
{req_summary}

Test case type coverage: {type_summary}
Automation feasibility: {automation_line}
Effort estimation: {estimation_line}

RULES:
- Output ONLY valid JSON
- No markdown
- No explanation
- Keep every text field concise and professional (2-5 sentences for paragraphs)
- Provide 3-5 entry_criteria, 3-5 exit_criteria, and 3-5 risks that are realistic for THIS
  project's requirements (e.g. if a requirement involves licensing, include a risk about
  license/environment availability during testing)

JSON shape:
{{
  "introduction": "1-2 sentence purpose of this document for this specific project",
  "objectives": "paragraph describing the testing objectives for this project",
  "test_approach_narrative": "paragraph explaining the test approach/levels used, referencing the type coverage above",
  "automation_narrative": "paragraph explaining the automation strategy, referencing the automation feasibility numbers above",
  "entry_criteria": ["...", "..."],
  "exit_criteria": ["...", "..."],
  "risks": [{{"risk": "...", "mitigation": "..."}}]
}}
""",
        expected_output="JSON object with the test strategy narrative sections",
        agent=strategy_writer,
    )

    crew = Crew(agents=[strategy_writer], tasks=[task], verbose=True, memory=False)
    print("🚀 Writing test strategy narrative...")
    try:
        crew.kickoff()
    except Exception as e:
        # Fall back to the default narrative text (defined below) rather than failing
        # the whole document just because the LLM narrative call didn't come back clean.
        print(f"⚠️ Test strategy narrative generation failed, using defaults: {e}")

    narrative = extract_json(task.output) or {}

    doc = Document()

    title = doc.add_heading("Test Strategy Document", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = doc.add_paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("1. Introduction", level=1)
    doc.add_paragraph(safe(narrative.get("introduction")) or
                       "This document defines the test strategy for the project based on the analyzed requirements.")

    doc.add_heading("2. Scope & Objectives", level=1)
    doc.add_paragraph("In Scope:")
    if requirement_items:
        _add_bullets(doc, [f'{r["req_id"]}: {r["requirement"]}' for r in requirement_items])
    else:
        _add_bullets(doc, ["No requirements were extracted."])
    doc.add_paragraph("Objectives:")
    doc.add_paragraph(safe(narrative.get("objectives")) or
                       "Validate that the system meets the documented requirements with adequate quality and risk coverage.")

    doc.add_heading("3. Test Approach", level=1)
    doc.add_paragraph(safe(narrative.get("test_approach_narrative")) or
                       "A mix of functional and non-functional testing types is applied based on requirement characteristics.")
    if type_counts:
        _add_table(doc, ["Test Type", "Test Case Count"],
                   sorted(type_counts.items(), key=lambda x: -x[1]))

    doc.add_heading("4. Automation Approach", level=1)
    doc.add_paragraph(safe(narrative.get("automation_narrative")) or
                       "Test cases suitable for automation are identified and mapped to the appropriate tool.")
    if automation_summary:
        doc.add_paragraph(
            f'Automatable: {automation_summary["automatable"]}/{automation_summary["total"]} '
            f'({automation_summary["coverage_pct"]}%)  |  Manual: {automation_summary["manual"]}'
        )
        if automation_summary["tool_counts"]:
            _add_table(doc, ["Recommended Tool", "Test Case Count"],
                       sorted(automation_summary["tool_counts"].items(), key=lambda x: -x[1]))
    else:
        doc.add_paragraph("Automation feasibility data not available.")

    doc.add_heading("5. Effort Estimation & Schedule", level=1)
    if estimation:
        _add_table(doc, ["Metric", "Value"], [
            ("Total Test Cases", estimation.get("total_test_cases", "-")),
            ("Test Cases / Day", estimation.get("test_cases_per_day", "-")),
            ("Estimated Days", estimation.get("estimated_days", "-")),
        ])
    else:
        doc.add_paragraph("Estimation data not available.")

    doc.add_heading("6. Roles & Responsibilities", level=1)
    _add_table(doc, ["Role", "Responsibilities"], ROLES_AND_RESPONSIBILITIES)

    doc.add_heading("7. Deliverables", level=1)
    _add_bullets(doc, DELIVERABLES)

    if traceability:
        doc.add_heading("Requirement Traceability Matrix", level=2)
        req_text_lookup = {r["req_id"]: r["requirement"] for r in requirement_items}
        _add_table(doc, ["Req ID", "Requirement", "Test Case IDs"], [
            (req_id, req_text_lookup.get(req_id, ""), ", ".join(tc_ids))
            for req_id, tc_ids in traceability.items()
        ], style="Table Grid")

    doc.add_heading("8. Entry & Exit Criteria", level=1)
    doc.add_paragraph("Entry Criteria:")
    _add_bullets(doc, narrative.get("entry_criteria") or DEFAULT_ENTRY_CRITERIA)
    doc.add_paragraph("Exit Criteria:")
    _add_bullets(doc, narrative.get("exit_criteria") or DEFAULT_EXIT_CRITERIA)

    doc.add_heading("9. Risks & Mitigation", level=1)
    risks = narrative.get("risks") or DEFAULT_RISKS
    _add_table(doc, ["Risk", "Mitigation"], [(safe(r.get("risk")), safe(r.get("mitigation"))) for r in risks])

    doc.add_heading("10. Metrics & Reporting", level=1)
    doc.add_paragraph("KPIs tracked:")
    _add_bullets(doc, KPIS)
    doc.add_paragraph("Reporting cadence & format:")
    _add_bullets(doc, REPORTING_CADENCE)
    tools_used = ", ".join((automation_summary or {}).get("tool_counts", {}).keys()) or "N/A"
    doc.add_paragraph(
        f"Tools: {tools_used} for automation; Excel-based reports generated by this QA pipeline "
        f"for requirements, test cases, review and estimation."
    )

    path = os.path.join(output_dir, f"test_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")
    doc.save(path)
    print(f"📄 Test strategy document saved to {path}")

    return path


if __name__ == "__main__":
    print("🚀 Script started")
    requirements = load_requirements_auto()
    print("✅ Requirements loaded")
    run_pipeline(requirements)
