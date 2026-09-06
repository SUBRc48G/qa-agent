# TestSprite Testing Guide

## What is TestSprite?

TestSprite is an **AI-powered automated testing platform** that uses Claude to:

1. **Test web applications automatically** - It visits your app's UI and performs test actions
2. **Generate test cases** - It can create test scenarios from your requirements
3. **Perform end-to-end testing** - Simulate real user flows and interactions

---

## How TestSprite Works in Your Project

### Architecture Flow

```
Your Streamlit App (localhost:8501)
    ↓
ngrok creates public HTTPS URL
    ↓
TestSprite accesses app via public URL
    ↓
TestSprite runs automated tests
    ↓
Generates test reports
```

---

## What Your QA Agent + TestSprite Does

Your project has a **Streamlit QA Test Case Generator**. When you use TestSprite MCP to test it:

### 1. Upload Requirements
- TestSprite uploads a requirements file (PDF, DOCX, XLSX, or TXT)

### 2. Trigger Pipeline
Your QA agent pipeline runs through these stages:
- **Analyzes requirements** - Breaks down into itemized list
- **Generates test cases** - Creates comprehensive test scenarios
- **Reviews & fixes test cases** - Improves quality and coverage
- **Assesses automation feasibility** - Determines which tests can be automated
- **Estimates effort** - Calculates testing timeline

### 3. Verify Outputs
TestSprite checks that:
- ✓ Progress indicators work correctly
- ✓ Test case reports are generated
- ✓ Excel files download properly
- ✓ Word files download properly
- ✓ Test Strategy document is created
- ✓ Error handling works for unsupported files

---

## Your Test Configuration

### Test Scope

| Item | Value |
|------|-------|
| Testing Type | Frontend (Streamlit UI) |
| Scope | Codebase (QA agent logic) |
| Application URL | `https://your-ngrok-url.ngrok-free.app` |
| Login Required | None |
| Test Files Location | `testsprite_tests/` folder |

### Test Plan Coverage

TestSprite will validate:
- [ ] Open the application
- [ ] Upload a .txt, .docx, .xlsx, or .pdf requirements file
- [ ] Verify pipeline progress indicators
- [ ] Verify generated test case reports
- [ ] Verify Excel downloads work
- [ ] Verify Word downloads work
- [ ] Verify Test Strategy generation
- [ ] Verify error handling for unsupported files

---

## Prerequisites

Before running TestSprite tests, ensure:

✅ **All 205 unit tests pass**
```powershell
.\.venv312\Scripts\python.exe -m pytest
```

✅ **Node.js v22+ installed**
```powershell
node --version
```

✅ **ngrok installed**
```powershell
ngrok --version
```

✅ **API_KEY in .env file**
- The `.env` file already has `API_KEY=sk-user-...` configured
- VS Code MCP configuration will load it automatically

---

## How to Run TestSprite Tests

### Step 1: Start Streamlit App (Terminal 1)
```powershell
cd C:\projects\qa-agent
.\.venv312\Scripts\python.exe -m streamlit run .\app.py --server.address 0.0.0.0 --server.port 8501
```

### Step 2: Start ngrok (Terminal 2)
```powershell
ngrok http 8501
```
**Copy the HTTPS URL shown** (e.g., `https://abc-123-def.ngrok-free.app`)

### Step 3: Configure TestSprite in VS Code

The MCP configuration is in `.vscode/mcp.json`:
```json
{
  "servers": {
    "testsprite": {
      "command": "npx",
      "args": ["-y", "@testsprite/testsprite-mcp@latest"],
      "envFile": "${workspaceFolder}/.env"
    }
  }
}
```

This automatically loads your `API_KEY` from `.env`

### Step 4: Use TestSprite MCP in Copilot Chat

Open VS Code Copilot Chat and send:

```
Can you test this project with TestSprite MCP?

The application is a Streamlit QA Test Case Generator.
Use this public URL: https://your-ngrok-url.ngrok-free.app

Test the complete user flow:
- Open the application
- Upload a .txt, .docx, .xlsx, or .pdf requirements file
- Verify pipeline progress
- Verify generated test case reports
- Verify Excel and Word downloads
- Verify Test Strategy generation
- Verify error handling for unsupported files
```

### Step 5: Monitor Progress

TestSprite will:
- Automate UI interactions with your app
- Verify expected results
- Generate test reports in `testsprite_tests/` folder
- Show pass/fail status for each test

### Step 6: Cleanup

When testing is complete:
```powershell
# Terminal 2 (ngrok): Press Ctrl+C
# Terminal 1 (Streamlit): Press Ctrl+C
```

Both terminals will stop, and the temporary public URL becomes invalid.

---

## Expected Test Reports

TestSprite generates reports in the `testsprite_tests/` folder:
- **Test execution logs** - Details of each test action
- **Screenshots** - Visual evidence of test steps
- **Pass/Fail summary** - Overall test results
- **Error reports** - Details of any failures

---

## What Gets Tested

### User Flow Validation

1. **Application loads** - UI renders correctly
2. **File upload works** - Can upload requirements files
3. **Pipeline executes** - Each stage completes successfully
4. **Reports generate** - Excel/Word files are created
5. **Downloads work** - Files can be downloaded from browser
6. **Error handling** - Unsupported files show proper error messages

### Data Flow Validation

1. **Requirements analyzed** - Parsed correctly into itemized list
2. **Test cases generated** - Comprehensive coverage of requirements
3. **Automation assessment** - Tools and feasibility determined
4. **Effort estimated** - Realistic timeline calculated

---

## Key Benefits

| Benefit | Details |
|---------|---------|
| **Automated** | No manual testing needed |
| **Comprehensive** | Tests entire user journey |
| **Evidence-based** | Screenshots and logs for each step |
| **Repeatable** | Run same tests any time |
| **Integration** | Tests full pipeline end-to-end |
| **AI-driven** | Claude evaluates test results intelligently |

---

## Configuration Files

### `.env` (Contains credentials)
```
API_KEY=sk-user-yGr1QsJCtifwDeLv_OTz2uJRCAc763SWOkm1HCMXnWpDMxQFDtUoDpICneCOewTCCY-pXQwfIRRpn8kEKlFoOBc_uV7MiEFFc7szoi8BBOAIP4v0fJEYpwBbVbr_GHGFB_M
OPENAI_API_KEY=sk-proj-...
```

### `.vscode/mcp.json` (MCP server config)
```json
{
  "servers": {
    "testsprite": {
      "command": "npx",
      "args": ["-y", "@testsprite/testsprite-mcp@latest"],
      "envFile": "${workspaceFolder}/.env"
    }
  }
}
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| ngrok URL not accessible | Ensure ngrok terminal is still running |
| API_KEY not found | Check `.env` file has `API_KEY=...` line |
| Tests fail to start | Verify Streamlit app is running on port 8501 |
| File downloads fail | Check browser download settings |
| MCP not connecting | Restart VS Code and reload MCP server |

---

## Status Summary

✅ **All 205 unit tests passed**
✅ **Streamlit app runs on port 8501**
✅ **Node.js v24.19.0 installed**
✅ **ngrok available**
✅ **API_KEY configured in .env**
✅ **MCP configuration ready**

**You're all set to run TestSprite automated tests!** 🚀

---

**Last Updated:** 2026-09-06
**Project:** QA Test Case Generator
**Status:** Ready for TestSprite Testing
