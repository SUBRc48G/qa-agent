import os
import html
import time
import tempfile
from datetime import datetime

import streamlit as st

from agent import load_requirements, run_pipeline, generate_test_strategy, default_testcases_per_day

st.set_page_config(page_title="QA Test Case Generator", page_icon="🧪", layout="wide")

# ---------------- STYLE ----------------

CATEGORICAL_PALETTE = [
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
]

STATUS = {
    "good": {"hex": "#0ca30c", "bg": "#e6f6e6", "icon": "✅"},
    "warning": {"hex": "#b3790a", "bg": "#fdf1da", "icon": "⚠️"},
    "serious": {"hex": "#ec835a", "bg": "#fdeae3", "icon": "🔧"},
}

CUSTOM_CSS = """
<style>
html, body, [class*="css"] { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }

.qa-hero {
    background: linear-gradient(135deg, #2a78d6 0%, #4a3aa7 100%);
    padding: 2rem 2.25rem;
    border-radius: 16px;
    color: #ffffff;
    margin-bottom: 1.25rem;
    box-shadow: 0 8px 24px rgba(42, 120, 214, 0.25);
}
.qa-hero h1 { margin: 0 0 0.4rem 0; font-size: 1.9rem; }
.qa-hero p { margin: 0; opacity: 0.92; font-size: 1rem; }

.qa-steps { display: flex; gap: 0.75rem; margin-bottom: 1.25rem; }
.qa-step {
    flex: 1; display: flex; align-items: center; gap: 0.6rem;
    padding: 0.7rem 1rem; border-radius: 12px; border: 1px solid #e1e0d9;
    background: #fcfcfb;
}
.qa-step.done { background: #eef6ee; border-color: #bfe3bf; }
.qa-step.active { background: #eaf2fc; border-color: #a9c9f2; }
.qa-step-badge {
    width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 600; background: #c3c2b7; color: #ffffff;
}
.qa-step.done .qa-step-badge { background: #0ca30c; }
.qa-step.active .qa-step-badge { background: #2a78d6; }
.qa-step-label { font-size: 0.88rem; font-weight: 600; color: #0b0b0b; }
.qa-step-sub { font-size: 0.76rem; color: #52514e; }

[data-testid="stMetric"] {
    background: #fcfcfb; border: 1px solid #e1e0d9; border-radius: 12px;
    padding: 0.9rem 1rem 0.6rem 1rem;
}

.qa-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.3rem 0.7rem; border-radius: 999px; font-size: 0.82rem; font-weight: 600;
}

.qa-bar-row { display: flex; align-items: center; gap: 0.6rem; margin: 0.45rem 0; }
.qa-bar-label { width: 150px; flex-shrink: 0; font-size: 0.85rem; color: #0b0b0b; text-align: right; }
.qa-bar-track { flex: 1; background: #e1e0d9; border-radius: 6px; height: 14px; overflow: hidden; }
.qa-bar-fill { height: 100%; border-radius: 6px; }
.qa-bar-count { width: 34px; flex-shrink: 0; font-variant-numeric: tabular-nums; font-size: 0.85rem; color: #52514e; }

.qa-danger-marker + div[data-testid="stButton"] button {
    background-color: #d03b3b !important; border-color: #d03b3b !important; color: #ffffff !important;
}
.qa-danger-marker + div[data-testid="stButton"] button:hover {
    background-color: #b32f2f !important; border-color: #b32f2f !important;
}

div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2a78d6 0%, #4a3aa7 100%);
    border: none; box-shadow: 0 4px 12px rgba(42, 120, 214, 0.3);
}
div.stButton > button[kind="primary"]:hover { opacity: 0.92; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_hero():
    st.markdown(
        """
        <div class="qa-hero">
            <h1>🧪 QA Test Case Generator</h1>
            <p>Upload a requirements document and let the QA crew analyze it, generate test cases,
            review/fix them, assess automation feasibility, estimate effort, and draft a test strategy.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_steps(uploaded, result, strategy_path):
    steps = [
        ("1", "Upload Requirements", "Word, Excel, PDF or text"),
        ("2", "Run QA Analysis", "Analyze, generate, review & estimate"),
        ("3", "Create Test Strategy", "Download the strategy document"),
    ]
    states = []
    if result:
        states = ["done", "done" if strategy_path else "active", "done" if strategy_path else "pending"]
    elif uploaded:
        states = ["done", "active", "pending"]
    else:
        states = ["active", "pending", "pending"]

    cells = []
    for (num, label, sub), state in zip(steps, states):
        css_state = state if state in ("done", "active") else ""
        badge = "✓" if state == "done" else num
        cells.append(
            f'<div class="qa-step {css_state}">'
            f'<div class="qa-step-badge">{badge}</div>'
            f'<div><div class="qa-step-label">{label}</div>'
            f'<div class="qa-step-sub">{sub}</div></div></div>'
        )
    st.markdown(f'<div class="qa-steps">{"".join(cells)}</div>', unsafe_allow_html=True)


def render_automation_bars(tool_counts):
    items = sorted(tool_counts.items(), key=lambda x: -x[1])
    if len(items) > 8:
        head, tail = items[:7], items[7:]
        items = head + [("Other", sum(c for _, c in tail))]

    max_count = max((c for _, c in items), default=1)
    rows = []
    for i, (tool, count) in enumerate(items):
        color = CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)]
        pct = max(6, round((count / max_count) * 100))
        rows.append(
            '<div class="qa-bar-row">'
            f'<div class="qa-bar-label">{html.escape(str(tool))}</div>'
            f'<div class="qa-bar-track"><div class="qa-bar-fill" style="width:{pct}%; background:{color};"></div></div>'
            f'<div class="qa-bar-count">{count}</div>'
            '</div>'
        )
    st.markdown("".join(rows), unsafe_allow_html=True)


def render_coverage_badge(pct):
    if pct >= 70:
        tier, text = "good", "High automation coverage"
    elif pct >= 40:
        tier, text = "warning", "Moderate automation coverage"
    else:
        tier, text = "serious", "Low automation coverage"

    s = STATUS[tier]
    st.markdown(
        f'<span class="qa-badge" style="background:{s["bg"]}; color:{s["hex"]};">'
        f'{s["icon"]} {text}</span>',
        unsafe_allow_html=True,
    )


# ---------------- SIDEBAR ----------------

OUTPUTS_ROOT = "outputs"

FILE_ICONS = {
    "requirements_analysis": "📋",
    "test_cases": "🧾",
    "review_comments": "🔍",
    "final": "✅",
    "automation_feasibility": "🤖",
    "estimation": "📅",
    "test_strategy": "📝",
}


def _file_icon(filename):
    for prefix, icon in FILE_ICONS.items():
        if filename.startswith(prefix):
            return icon
    return "📄"


with st.sidebar:
    st.markdown("### 🧪 QA Agent")
    st.caption("AI-powered requirement analysis & test case generation")
    st.divider()

    st.markdown("**📂 Run History**")
    if os.path.isdir(OUTPUTS_ROOT):
        run_dirs = sorted(
            (d for d in os.listdir(OUTPUTS_ROOT) if os.path.isdir(os.path.join(OUTPUTS_ROOT, d))),
            reverse=True,
        )
    else:
        run_dirs = []

    if run_dirs:
        selected_run = st.selectbox("Past runs", run_dirs, index=0)
        run_path = os.path.join(OUTPUTS_ROOT, selected_run)
        for fname in sorted(os.listdir(run_path)):
            fpath = os.path.join(run_path, fname)
            with open(fpath, "rb") as f:
                st.download_button(
                    f"{_file_icon(fname)} {fname}",
                    data=f.read(),
                    file_name=fname,
                    key=f"hist_{selected_run}_{fname}",
                    use_container_width=True,
                )
    else:
        st.caption("No past runs yet — they'll show up here after you run the analysis.")

    st.divider()
    st.markdown("**Session**")
    st.markdown('<div class="qa-danger-marker"></div>', unsafe_allow_html=True)
    if st.button("🛑 Exit App", use_container_width=True):
        st.warning("Shutting down the app server... you can close this browser tab.")
        time.sleep(1)
        os._exit(0)

# ---------------- MAIN ----------------

render_hero()

uploaded_file = st.file_uploader(
    "Upload requirements",
    type=["txt", "pdf", "docx", "xlsx"],
    help="Supported formats: Word (.docx), Excel (.xlsx), PDF (.pdf), Notepad/plain text (.txt)",
)

render_steps(uploaded_file, st.session_state.get("result"), st.session_state.get("strategy_path"))

testcases_per_day = st.number_input(
    "Test cases executable per day (used for effort estimation)",
    min_value=1,
    value=default_testcases_per_day,
    step=1,
)

generate = st.button("🚀 Run QA Analysis", type="primary", disabled=uploaded_file is None)

if generate and uploaded_file is not None:
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        requirements_text = load_requirements(tmp_path)
    finally:
        os.remove(tmp_path)

    if not requirements_text.strip():
        st.error("No text could be extracted from the uploaded file.")
    else:
        with st.expander("Extracted requirements text", expanded=False):
            st.text(requirements_text)

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("outputs", run_id)

        with st.status("Running the QA crew...", expanded=True) as status_box:
            def report_progress(message, _box=status_box):
                _box.write(message)

            result = run_pipeline(
                requirements_text,
                testcases_per_day=testcases_per_day,
                output_dir=output_dir,
                progress_callback=report_progress,
            )
            if result.get("warnings"):
                status_box.update(label="QA crew finished with warnings", state="error")
            else:
                status_box.update(label="QA crew finished", state="complete")

        st.session_state["result"] = result
        st.session_state.pop("strategy_path", None)
        st.rerun()

result = st.session_state.get("result")

if result:
    if result.get("warnings"):
        st.warning("Pipeline completed with issues:\n\n" + "\n".join(f"- {w}" for w in result["warnings"]))
    else:
        st.success("Pipeline completed")

    counts = result["counts"]
    with st.container(border=True):
        st.markdown("#### 📊 Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Requirements", counts["requirements"])
        col2.metric("Generated Test Cases", counts["generated_test_cases"])
        col3.metric("Final Test Cases", counts["final_test_cases"])

        automation = result.get("automation_summary")
        if automation:
            col4.metric(
                "Automatable",
                f'{automation["automatable"]}/{automation["total"]} ({automation["coverage_pct"]}%)',
            )

    if automation:
        with st.container(border=True):
            st.markdown("#### 🤖 Automation Feasibility")
            render_coverage_badge(automation["coverage_pct"])
            st.write("")
            if automation["tool_counts"]:
                render_automation_bars(automation["tool_counts"])
            else:
                st.write("No automatable test cases identified.")

    estimation = result.get("estimation")
    if estimation:
        with st.container(border=True):
            st.markdown("#### 📅 Effort Estimation")
            e1, e2, e3 = st.columns(3)
            e1.metric("Total Test Cases", estimation.get("total_test_cases", counts["final_test_cases"]))
            e2.metric("Test Cases / Day", estimation.get("test_cases_per_day", testcases_per_day))
            e3.metric("Estimated Days", estimation.get("estimated_days", "-"))

    with st.container(border=True):
        st.markdown("#### 📥 Download Reports")
        labels = {
            "requirements": "📋 Requirements Analysis",
            "test_cases": "🧾 Draft Test Cases",
            "review": "🔍 Review Comments",
            "final": "✅ Final Test Cases",
            "automation": "🤖 Automation Feasibility",
            "estimation": "📅 Effort Estimation",
        }

        cols = st.columns(3)
        for i, (key, label) in enumerate(labels.items()):
            path = result["files"].get(key)
            if path and os.path.exists(path):
                with open(path, "rb") as f:
                    cols[i % 3].download_button(
                        label=f"Download {label}",
                        data=f.read(),
                        file_name=os.path.basename(path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_{key}",
                        use_container_width=True,
                    )

    with st.container(border=True):
        st.markdown("#### 📝 Test Strategy Document")
        st.caption(
            "Generates a Word document covering scope & objectives, test approach, automation "
            "approach, effort estimation, roles & responsibilities, deliverables, entry/exit "
            "criteria, risks, and metrics/reporting — built from this run's results."
        )

        if st.button("📝 Create Test Strategy"):
            with st.spinner("Writing the test strategy document..."):
                strategy_path = generate_test_strategy(
                    requirement_items=result["data"]["requirements"],
                    final_test_cases=result["data"]["final_test_cases"],
                    automation_summary=result.get("automation_summary"),
                    estimation=result.get("estimation"),
                    output_dir=result["output_dir"],
                )
            st.session_state["strategy_path"] = strategy_path
            st.rerun()

        strategy_path = st.session_state.get("strategy_path")
        if strategy_path and os.path.exists(strategy_path):
            st.success("Test strategy document ready")
            with open(strategy_path, "rb") as f:
                st.download_button(
                    label="Download Test Strategy (.docx)",
                    data=f.read(),
                    file_name=os.path.basename(strategy_path),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="download_strategy",
                )
else:
    st.info("Upload a requirements file and click **Run QA Analysis** to get started.")
