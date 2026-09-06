# How to Generate a TestSprite Test Plan

## Overview

TestSprite **automatically generates a test plan** when you run it. It analyzes your application and creates:
- Automated test scenarios
- Test execution steps
- Expected results
- Test reports with evidence (screenshots, logs)

---

## 3 Ways to Get a TestSprite Test Plan

### Method 1: Run TestSprite via VS Code Copilot Chat (RECOMMENDED)

#### Step 1: Setup Streamlit + ngrok
Open two terminals:

**Terminal 1 - Start Streamlit:**
```powershell
cd C:\projects\qa-agent
.\.venv312\Scripts\python.exe -m streamlit run .\app.py --server.address 0.0.0.0 --server.port 8501
```

**Terminal 2 - Start ngrok:**
```powershell
ngrok http 8501
```
Copy the HTTPS URL (e.g., `https://abc-123-xyz.ngrok-free.app`)

#### Step 2: Request TestSprite Test Plan in Copilot Chat

Open VS Code **Copilot Chat** and send:

```
Can you create a TestSprite test plan for this application?

Application: Streamlit QA Test Case Generator
URL: https://your-ngrok-url-here.ngrok-free.app
API_KEY: [Will load from .env]

Please:
1. Analyze the application UI
2. Identify all user interactions available
3. Create automated test scenarios
4. Execute the tests
5. Generate a test report

Test the following flows:
- Upload a PDF requirements file
- Upload an Excel requirements file
- Verify pipeline execution
- Download generated Excel files
- Check error handling
```

#### Step 3: TestSprite Will:
✅ Automatically visit your application
✅ Test every UI element
✅ Upload sample requirement files
✅ Verify all outputs
✅ Take screenshots of each step
✅ Generate test report in `testsprite_tests/` folder

#### Step 4: View the Generated Test Plan

TestSprite creates these files in `testsprite_tests/`:
```
testsprite_tests/
├── test_execution_log.html          (Detailed step-by-step log)
├── test_report.json                 (Structured test results)
├── screenshots/
│   ├── step_1_app_load.png
│   ├── step_2_file_upload.png
│   ├── step_3_pipeline_progress.png
│   └── step_4_download.png
└── test_summary.md                  (Human-readable summary)
```

---

### Method 2: Generate Test Plan Using TestSprite CLI

#### Install TestSprite CLI:
```powershell
npm install -g @testsprite/testsprite-cli
```

#### Create a test configuration file `testsprite-config.json`:
```json
{
  "application": {
    "name": "QA Test Case Generator",
    "url": "https://your-ngrok-url.ngrok-free.app",
    "type": "streamlit"
  },
  "testing": {
    "type": "e2e",
    "browser": "chromium",
    "headless": false,
    "timeout": 30000
  },
  "test_scenarios": [
    {
      "name": "Upload TXT Requirements",
      "steps": [
        "Open application",
        "Click file upload button",
        "Upload qa_requirements.txt",
        "Verify upload success"
      ]
    },
    {
      "name": "Generate and Download Test Cases",
      "steps": [
        "Wait for pipeline completion",
        "Verify progress indicators",
        "Click download test cases",
        "Verify Excel file downloaded"
      ]
    }
  ],
  "reports": {
    "output_dir": "testsprite_tests",
    "format": ["html", "json", "markdown"]
  }
}
```

#### Run TestSprite:
```powershell
testsprite run --config testsprite-config.json --api-key $env:API_KEY
```

---

### Method 3: Create a Custom Test Plan Manually

Create `CUSTOM_TEST_PLAN.md`:

```markdown
# Custom TestSprite Test Plan

## Test Scenario 1: Upload Requirements & Generate Test Cases

### Steps:
1. Open application at https://your-ngrok-url.ngrok-free.app
2. Wait for app to load completely
3. Click "Upload Requirements File" button
4. Select `qa_requirements.txt`
5. Verify file upload progress indicator appears
6. Wait for "Requirements analyzed" message
7. Verify test cases appear on screen
8. Click "Download Test Cases" button
9. Verify Excel file downloads to default folder
10. Verify file is valid Excel (.xlsx)

### Expected Results:
- ✓ File uploads without error
- ✓ Progress shows 6 stages completing
- ✓ Test cases display in table format
- ✓ Download button is clickable
- ✓ File downloads to Downloads folder
- ✓ File opens in Excel without corruption

### Screenshots to Capture:
- App loaded state
- File upload dialog
- Progress bar at each stage
- Final test cases table
- Download confirmation

---

## Test Scenario 2: Excel Report Validation

### Steps:
1. After test cases generated, examine Excel files created
2. Verify file structure and formatting
3. Check that all test data is present
4. Verify Excel formulas (if any) work

### Expected Results:
- ✓ All required columns present
- ✓ Test case IDs sequential
- ✓ No duplicate entries
- ✓ Cell styling applied (bold headers, wrapped text)

---

## Test Scenario 3: Error Handling

### Steps:
1. Try to upload an unsupported file (e.g., .zip)
2. Verify error message appears
3. Try to upload with incomplete data
4. Verify appropriate error

### Expected Results:
- ✓ Clear error messages shown
- ✓ Application doesn't crash
- ✓ User can try again

---

## Test Environment
- Browser: Chrome/Edge
- OS: Windows 11
- Screen Resolution: 1920x1080
- Network: ngrok tunnel to localhost:8501
```

---

## Interpreting TestSprite Test Reports

### HTML Report Structure

```html
<div class="test-execution">
  <h1>TestSprite Execution Report</h1>
  
  <!-- Summary Stats -->
  <div class="summary">
    Tests Executed: 8
    Tests Passed: 7
    Tests Failed: 1
    Duration: 2m 34s
    Coverage: 94%
  </div>
  
  <!-- Detailed Steps -->
  <div class="test-steps">
    <div class="step passed">
      <h3>Step 1: Open Application</h3>
      <img src="screenshots/step_1.png">
      <p>Status: ✅ PASS</p>
      <p>Duration: 3s</p>
    </div>
    ...
  </div>
</div>
```

### JSON Report Format

```json
{
  "test_plan": {
    "application": "QA Test Case Generator",
    "url": "https://example.ngrok-free.app",
    "timestamp": "2026-09-06T10:30:00Z"
  },
  "test_executions": [
    {
      "scenario": "Upload Requirements",
      "steps": 5,
      "passed": 5,
      "failed": 0,
      "duration": "12.5s",
      "screenshots": ["step_1.png", "step_2.png"],
      "evidence": "File uploaded successfully"
    }
  ],
  "summary": {
    "total_tests": 8,
    "passed": 7,
    "failed": 1,
    "pass_rate": "87.5%"
  }
}
```

### Markdown Report Example

```markdown
# TestSprite Test Execution Report
Generated: 2026-09-06 10:30 AM

## Summary
- **Total Scenarios:** 3
- **Total Steps:** 15
- **Passed:** 14 ✅
- **Failed:** 1 ❌
- **Duration:** 2m 34s
- **Success Rate:** 93%

## Scenario 1: Upload Requirements File
✅ **Status:** PASSED

| Step | Action | Result | Evidence |
|------|--------|--------|----------|
| 1 | Open app | Page loaded (3s) | screenshot_1.png |
| 2 | Click upload | Dialog opened | screenshot_2.png |
| 3 | Select file | qa_requirements.txt selected | screenshot_3.png |
| 4 | Submit | File uploaded | screenshot_4.png |
| 5 | Verify | Success message shown | screenshot_5.png |

## Scenario 2: Generate Test Cases
✅ **Status:** PASSED

...

## Scenario 3: Error Handling
❌ **Status:** FAILED (1 step)

| Step | Issue | Expected | Actual |
|------|-------|----------|--------|
| 1 | Unsupported file error | "Invalid file type" | No error shown |

### Recommendations:
- Fix error handling for .zip files
- Add file type validation before upload
```

---

## What TestSprite Test Plan Includes

### 1. **Pre-Execution Analysis**
```
Application Scan:
├── UI Elements Found: 24
├── Forms: 2
├── Buttons: 8
├── File Inputs: 1
├── Download Links: 3
└── Error Messages: 2 placeholder areas
```

### 2. **Auto-Generated Test Scenarios**
```
Scenario 1: Happy Path (Valid Input)
  ├── Upload valid requirements
  ├── Trigger pipeline
  ├── Verify outputs
  └── Download results

Scenario 2: Alternative Path (Different File Format)
  ├── Upload .docx file
  ├── Verify processing
  └── Check results

Scenario 3: Error Path (Invalid Input)
  ├── Upload invalid file
  ├── Verify error message
  └── Verify recovery
```

### 3. **Step-by-Step Execution Log**
```
[10:30:15] Step 1: Navigate to https://...ngrok-free.app
           Status: ✅ PASS (2.3s)
           
[10:30:18] Step 2: Wait for page load
           Status: ✅ PASS (3.1s)
           
[10:30:22] Step 3: Locate file upload element
           Status: ✅ PASS (0.5s)
           
...
```

### 4. **Screenshot Evidence**
```
Step 1: Application Loaded
├─ screenshot_1_full_page.png
├─ screenshot_1_header.png
└─ screenshot_1_file_input.png

Step 2: File Upload Dialog
├─ screenshot_2_dialog.png
└─ screenshot_2_file_selected.png

Step 3: Upload Progress
├─ screenshot_3_progress_bar.png
└─ screenshot_3_upload_complete.png
```

### 5. **Test Results Summary**
```
┌─────────────────────────────────────┐
│      TEST EXECUTION SUMMARY         │
├─────────────────────────────────────┤
│ Total Test Cases:        12         │
│ Passed:                  11  ✅     │
│ Failed:                   1  ❌     │
│ Skipped:                  0         │
│ Total Duration:          2m 45s     │
│ Success Rate:           91.7%       │
└─────────────────────────────────────┘
```

### 6. **Detailed Failure Reports**
```
Failed Test: "Error Handling - Invalid File Type"

Step: Upload .zip file
Expected: Show error "Unsupported file format"
Actual: No error shown, file accepted

Severity: MEDIUM
Impact: User confusion if .zip uploaded
Recommendation: Add file type validation before upload

Evidence:
├─ screenshot_error_1.png (What was expected)
├─ screenshot_error_2.png (What actually happened)
└─ console_log.txt (Browser console output)
```

---

## Quick Start: Generate Test Plan in 5 Minutes

```powershell
# Terminal 1
cd C:\projects\qa-agent
.\.venv312\Scripts\python.exe -m streamlit run .\app.py --server.address 0.0.0.0 --server.port 8501

# Terminal 2
ngrok http 8501
# Wait 10 seconds, copy the HTTPS URL

# VS Code Copilot Chat
# Send the TestSprite request (see Method 1 above)

# Wait 2-5 minutes for TestSprite to complete...

# View results
# Open: testsprite_tests/test_report.html
```

---

## File Structure After TestSprite Run

```
project-root/
├── testsprite_tests/              (Created by TestSprite)
│   ├── test_execution.html        (Detailed report)
│   ├── test_report.json           (Machine-readable)
│   ├── test_summary.md            (Human-readable)
│   ├── screenshots/
│   │   ├── step_1_app_load.png
│   │   ├── step_2_upload.png
│   │   ├── step_3_pipeline.png
│   │   └── step_4_download.png
│   ├── logs/
│   │   ├── browser_console.log
│   │   ├── network_requests.log
│   │   └── performance.log
│   └── evidence/
│       ├── uploaded_file.xlsx
│       ├── downloaded_file.xlsx
│       └── validation_results.json
```

---

## Next Steps After Getting Test Plan

1. **Review Report** - Open `test_execution.html` in browser
2. **Check Screenshots** - Verify expected application behavior
3. **Fix Failures** - Address any failed test steps
4. **Document Findings** - Keep test plan for regression testing
5. **Re-run if Needed** - Run TestSprite again after fixes
6. **Archive Report** - Save for audit trail

---

## Cost & Time Estimate

| Item | Time | Cost |
|------|------|------|
| Streamlit startup | 5s | $0 |
| ngrok tunnel | 5s | $0 |
| TestSprite analysis | 30s | $0 |
| Test execution | 2-3m | $0-0.50 |
| Report generation | 10s | $0 |
| **TOTAL** | **2-4 min** | **$0-0.50** |

---

**Ready to generate your TestSprite test plan?** Start with Method 1 above! 🚀
