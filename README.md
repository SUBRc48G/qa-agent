# QA Test Case Generator

An AI-powered QA assistant that turns a raw requirements document into a full test
package — analyzed requirements, generated test cases, a reviewed/fixed final set,
an automation feasibility assessment, an effort estimate, and a Word test strategy
document — with a simple drag-and-drop web UI on top.

## What it does

1. **You upload requirements** — Word (`.docx`), Excel (`.xlsx`), PDF (`.pdf`), or
   plain text (`.txt`).
2. **A crew of AI agents works through them in sequence**, each one specialized in
   one part of the QA process (see below).
3. **You get back a set of downloadable reports** (Excel + Word) plus a live
   dashboard summarizing coverage, automation feasibility, and effort.

No manual test design required to get a first complete draft — the app does the
requirement breakdown, test design, peer review, automation assessment, and
estimation for you, and a human can then refine the output.

## The overall flow

```
Upload requirements
        │
        ▼
1. Analyst          → breaks requirements into an itemized, structured list
        │
        ▼
2. QA Engineer       → generates test cases covering every requirement
        │              (positive, negative, edge, security, performance,
        │               usability, compatibility, integration, etc.)
        ▼
3. Reviewer          → reviews the draft test cases, leaves comments
        │
        ▼
4. Fixer             → applies the review feedback, produces the final test cases
        │
        ▼
5. Automation Analyst → decides which final test cases can be automated and
        │               which tool/framework fits each one (Selenium, Playwright,
        │               Appium, Postman, JMeter, etc.)
        ▼
6. Estimator         → estimates total effort (days) to execute the test cases
        │
        ▼
(optional) QA Lead   → writes a full Test Strategy Word document, combining all
                        of the above into one shareable artifact
```

Each stage's output feeds into the next one as context, so later agents build on
what earlier agents produced rather than starting from scratch.

## Why CrewAI

The pipeline is built on [CrewAI](https://www.crewai.com/), a framework for
orchestrating multiple LLM-powered agents that collaborate on a chain of tasks.
In this app:

- Each **role** above (Analyst, QA Engineer, Reviewer, Fixer, Automation Analyst,
  Estimator, and the QA Lead for the strategy doc) is a CrewAI `Agent` — it has a
  role, a goal, and a backstory that shapes how it approaches its part of the job.
- Each step in the flow is a CrewAI `Task` — a specific instruction given to one
  agent, with the previous tasks' outputs wired in as `context` so information
  flows forward through the pipeline.
- All the tasks for one run are bundled into a single `Crew`, which executes them
  in order and hands off outputs automatically.
- **Guardrails**: every task that must return structured JSON has a guardrail
  attached. If an agent's response isn't valid JSON, CrewAI automatically asks it
  to retry (up to a few times) before giving up — this makes the pipeline
  noticeably more resilient to an LLM occasionally returning malformed output.
- **Progress callbacks**: the crew reports back after each task finishes, which is
  what powers the live "✅ Test cases generated..." progress you see in the UI
  while a run is in progress.

If any stage still can't produce usable output after retrying, the pipeline
doesn't crash — it keeps going with whatever succeeded and surfaces a clear
warning in the UI (and the corresponding report is simply skipped) instead of
failing the whole run.

## What you get back

| Report | Contents |
|---|---|
| Requirements Analysis (`.xlsx`) | The itemized requirement list (ID, description, category, priority) |
| Draft Test Cases (`.xlsx`) | Test cases as first generated |
| Review Comments (`.xlsx`) | Reviewer feedback per test case |
| Final Test Cases (`.xlsx`) | The fixed/approved test cases, with an Automatable column |
| Automation Feasibility (`.xlsx`) | Per-test-case automation verdict + recommended tool, plus a summary sheet (coverage %, tool breakdown) |
| Effort Estimation (`.xlsx`) | Total test cases, cases/day, estimated days |
| Test Strategy (`.docx`) | Scope & objectives, test approach, automation approach, estimation, roles & responsibilities, deliverables, traceability matrix, entry/exit criteria, risks, and metrics/reporting — one shareable document |

## The web UI

Built with [Streamlit](https://streamlit.io/). It gives you:

- A file uploader for the requirements document
- A live status panel showing progress as the crew works through each stage
- A results dashboard (requirement/test case counts, automation coverage badge and
  tool breakdown, estimation figures)
- Download buttons for every report above
- A one-click **Create Test Strategy** action once a run has completed
- A **Run History** panel in the sidebar to revisit and re-download reports from
  past runs
- An **Exit** control to shut the app down from the browser

## Running it on Windows

Follow these steps from PowerShell. Python 3.12 is recommended because the
project's AI dependencies may not install correctly on Python 3.14.

### 1. Open the project folder

```powershell
cd C:\projects\qa-agent
```

### 2. Create the virtual environment

Run this once:

```powershell
py -3.12 -m venv .venv312
```

### 3. Activate it and install dependencies

```powershell
.\.venv312\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install torchvision
```

`torchvision` is required by the Transformers version installed by the
`sentence-transformers` dependency.

If PowerShell blocks activation, skip activation and use the full interpreter
path in the commands below.

### 4. Create the `.env` file

Create a file named `.env` in the project folder with this content:

```text
OPENAI_API_KEY=replace-with-your-openai-api-key
MODEL_NAME=gpt-4o-mini
TEST_CASES_PER_DAY=20
```

Replace the placeholder with your actual OpenAI API key. Do not commit `.env`.

### 5. Start the application

If the environment is activated:

```powershell
python -m streamlit run .\app.py
```

If it is not activated:

```powershell
.\.venv312\Scripts\python.exe -m streamlit run .\app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser. The first
run may take longer because the embedding model is downloaded from Hugging Face.
Keep the terminal open while using the application. Press `Ctrl+C` in the
terminal to stop it.

### Troubleshooting

- **`No module named streamlit`**: use `.\.venv312\Scripts\python.exe` in the
        launch command instead of the system `python` command.
- **`No module named torchvision`**: run
        `python -m pip install torchvision` while `.venv312` is active.
- **`Missing OPENAI_API_KEY`**: check that `.env` is in `C:\projects\qa-agent`
        and that the key is not still the placeholder.

There is also a plain CLI mode for automation/scripting: `python agent.py` runs
the pipeline without the Streamlit UI.
