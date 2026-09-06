# Docker Testing Summary - Complete Guide

Complete end-to-end testing guide for QA Agent using Docker.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites Checklist](#prerequisites-checklist)
3. [Step-by-Step Testing](#step-by-step-testing)
4. [Test Results](#test-results)
5. [Integration with GitHub](#integration-with-github)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides a complete testing workflow for the QA Agent application using Docker containers. Tests include:

- ✅ **Unit Tests** (199 tests) - Test individual functions
- ✅ **Integration Tests** (7 tests) - Test full pipeline with real API
- ✅ **E2E Tests** (16 tests) - Test via browser automation
- ✅ **Code Quality** - Type checking, linting, coverage

**Total Coverage:** 92% of FRS requirements

---

## Prerequisites Checklist

### System Requirements

- [ ] Windows 11 or later (or Docker Desktop on Mac/Linux)
- [ ] Docker Desktop installed (version 24.0+)
- [ ] Docker Compose installed (version 2.0+)
- [ ] At least 4GB RAM available for containers
- [ ] At least 5GB disk space available

### Software Check

```powershell
# Run these commands to verify installation
docker --version       # Should show: Docker version 24.x or higher
docker-compose --version  # Should show: Docker Compose version 2.x or higher
python --version       # Should show: Python 3.12.x
git --version         # Should show: git version 2.x or higher
```

### Configuration Files

- [ ] `.env` file created with OPENAI_API_KEY
- [ ] `.streamlit/config.toml` configured
- [ ] `.gitignore` present (excludes unnecessary files)
- [ ] `.dockerignore` present (optimizes Docker build)

### Project Files

- [ ] `Dockerfile` - Application image definition
- [ ] `Dockerfile.tests` - Test runner image definition
- [ ] `docker-compose.yml` - Service orchestration
- [ ] `requirements.txt` - Python dependencies
- [ ] `requirements-dev.txt` - Development dependencies
- [ ] `test_e2e_playwright.py` - E2E tests (16 tests)
- [ ] `tests/` directory - Unit/integration tests (199 tests)

---

## Step-by-Step Testing

### Phase 1: Build Docker Images (5-10 minutes)

#### Step 1.1: Build Application Image

```powershell
# Navigate to project
cd C:\projects\qa-agent

# Build application image
docker build -t qa-agent:latest .

# Expected output:
# [+] Building 45.3s (15/15) FINISHED
# => exporting to image
# => naming to docker.io/library/qa-agent:latest
```

**Verify:**
```powershell
docker images | grep qa-agent
# Should show: qa-agent | latest | ... | 250MB
```

#### Step 1.2: Build Test Image

```powershell
# Build test runner image
docker build -f Dockerfile.tests -t qa-agent-tests:latest .

# This installs additional dependencies including Playwright

# Expected output:
# [+] Building 120.5s (12/12) FINISHED
# => exporting to image
# => naming to docker.io/library/qa-agent-tests:latest
```

**Verify:**
```powershell
docker images | grep qa-agent-tests
# Should show: qa-agent-tests | latest | ... | 850MB
```

**Time**: ~10 minutes total (varies with internet speed)

---

### Phase 2: Run Application (5 minutes)

#### Step 2.1: Start Application Container

```powershell
# Option A: Using Docker Compose (Recommended)
docker-compose up -d qa-agent

# Expected output:
# Creating network "qa-agent_qa-network" with driver "bridge"
# Creating qa-agent ... done

# Option B: Manual Docker
docker run -d \
  -p 8501:8501 \
  --env-file .env \
  --name qa-agent \
  qa-agent:latest
```

#### Step 2.2: Wait for Application to Start

```powershell
# Wait 10-15 seconds for Streamlit to initialize
Start-Sleep -Seconds 15

# Check if container is running
docker ps | grep qa-agent
# Should show: qa-agent | ... | Up 10 seconds | 0.0.0.0:8501->8501/tcp
```

#### Step 2.3: Verify Application Health

```powershell
# Check health endpoint
curl http://localhost:8501/_stcore/health

# Expected output:
# OK

# Or open in browser
Start-Process "http://localhost:8501"
```

**Troubleshooting:**
- If connection refused: Wait 20 seconds, then try again
- If port in use: Change to different port: `-p 9000:8501`
- Check logs: `docker logs -f qa-agent`

**Time**: ~20 seconds

---

### Phase 3: Run Unit Tests (2-3 minutes)

#### Step 3.1: Run All Unit Tests

```powershell
# Run unit tests only (excludes integration tests)
docker run --rm qa-agent-tests:latest \
  pytest tests/ -m "not integration" -v

# Expected output:
# tests/test_extract_json_advanced.py::test_extract_valid_json PASSED
# tests/test_extract_json_advanced.py::test_extract_invalid_json PASSED
# ... (199 tests)
# ===================== 199 passed in 15.23s ========================
```

#### Step 3.2: Check Results

```powershell
# Summary should show:
# - PASSED: 199 tests
# - FAILED: 0 tests
# - Time: ~15-20 seconds
```

#### Step 3.3: Generate Coverage Report (Optional)

```powershell
docker run --rm \
  -v C:\projects\qa-agent:/app \
  qa-agent-tests:latest \
  pytest tests/ -m "not integration" --cov=. --cov-report=html

# View report
# Open: htmlcov/index.html in browser
```

**Expected Coverage:** 80-90% for core functions

**Time**: ~15 seconds

---

### Phase 4: Run Integration Tests (5 minutes)

#### Step 4.1: Run Integration Tests

```powershell
# Integration tests use real OpenAI API
docker run --rm \
  --env-file .env \
  qa-agent-tests:latest \
  pytest tests/ -m integration -v

# Expected output:
# tests/test_pipeline_integration.py::test_full_pipeline PASSED
# tests/test_pipeline_integration.py::test_json_extraction PASSED
# ... (7 tests)
# ===================== 7 passed in 156.42s ======================
```

**Important:** 
- Requires valid OPENAI_API_KEY in .env
- Takes longer (5+ minutes) due to LLM calls
- Costs ~$1-2 per run

#### Step 4.2: Check Results

```powershell
# Summary should show:
# - PASSED: 7 tests
# - FAILED: 0 tests
# - Time: ~2-5 minutes
```

**Time**: ~5 minutes (depending on API latency)

---

### Phase 5: Run E2E Tests (10-15 minutes)

#### Step 5.1: Verify Application is Running

```powershell
# Application should still be running from Phase 2
docker ps | grep qa-agent

# If not running, restart:
docker-compose up -d qa-agent
Start-Sleep -Seconds 15
```

#### Step 5.2: Run E2E Tests

```powershell
# Run E2E tests using docker-compose
docker-compose run --rm qa-agent-tests \
  pytest test_e2e_playwright.py -v -s

# Expected output:
# TEST 1: Full Pipeline (TXT) - PASSED
# TEST 2: PDF Upload - PASSED
# TEST 3: Excel Upload - PASSED
# ... (16 tests)
# ================== 16 passed in 642.35s =====================
```

#### Step 5.3: Check Individual Test Results

```powershell
# Check specific test
docker-compose run --rm qa-agent-tests \
  pytest test_e2e_playwright.py::test_e2e_run_qa_analysis_button -v

# Expected:
# TEST 7: Run QA Analysis Button (Button State + Execution) - PASSED
```

#### Step 5.4: Test Reports

Tests should generate:
- Console output with step-by-step execution
- ✅ marks for passed assertions
- ⚠️ marks for warnings
- Timing for each test

**Time**: ~10-15 minutes (Tests 1, 8, 10, 15 wait for LLM)

---

### Phase 6: Complete Test Suite (20-25 minutes)

#### Step 6.1: Run Everything in Sequence

```powershell
# Complete test workflow
Write-Host "Step 1: Building images..."
docker build -t qa-agent:latest .
docker build -f Dockerfile.tests -t qa-agent-tests:latest .

Write-Host "Step 2: Starting application..."
docker-compose up -d qa-agent
Start-Sleep -Seconds 15

Write-Host "Step 3: Running unit tests..."
docker run --rm qa-agent-tests:latest pytest tests/ -m "not integration" -v

Write-Host "Step 4: Running integration tests..."
docker run --rm --env-file .env qa-agent-tests:latest pytest tests/ -m integration -v

Write-Host "Step 5: Running E2E tests..."
docker-compose run --rm qa-agent-tests pytest test_e2e_playwright.py -v

Write-Host "Step 6: Cleanup"
docker-compose down
```

#### Step 6.2: Verify All Tests Passed

**Expected Summary:**
```
✅ Unit Tests: 199 passed in 15s
✅ Integration Tests: 7 passed in 300s
✅ E2E Tests: 16 passed in 640s
✅ Total: 222 tests passed in ~1000s (16 minutes)
```

**Total Time**: ~25 minutes

---

## Test Results

### Expected Test Output

#### Unit Tests
```
============================== 199 passed in 15.23s ==============================
Tests from: tests/test_extract_json_advanced.py
            tests/test_error_handling.py
            tests/test_excel_reports.py
            ... (13 test files total)
```

#### Integration Tests
```
============================== 7 passed in 156.42s ===============================
Tests from: tests/test_pipeline_integration.py

Tests:
- test_full_pipeline: ✅ PASSED
- test_json_extraction: ✅ PASSED
- test_test_generation: ✅ PASSED
- test_review_and_fix: ✅ PASSED
- test_automation_assessment: ✅ PASSED
- test_effort_estimation: ✅ PASSED
- test_end_to_end_pipeline: ✅ PASSED
```

#### E2E Tests
```
============================== 16 passed in 642.35s ==============================
Tests from: test_e2e_playwright.py

Tests:
1. test_e2e_full_pipeline_with_txt_file: ✅ PASSED
2. test_e2e_upload_pdf_requirements: ✅ PASSED
3. test_e2e_upload_excel_requirements: ✅ PASSED
4. test_e2e_verify_progress_indicators: ✅ PASSED
5. test_e2e_download_excel_files: ✅ PASSED
6. test_e2e_verify_excel_contents: ✅ PASSED
7. test_e2e_run_qa_analysis_button: ✅ PASSED
8. test_e2e_complete_workflow: ✅ PASSED
9. test_e2e_upload_word_requirements: ✅ PASSED
10. test_e2e_generate_test_strategy_word: ✅ PASSED
11. test_e2e_error_unsupported_file_format: ✅ PASSED
12. test_e2e_error_file_size_exceeds_limit: ✅ PASSED
13. test_e2e_test_cases_per_day_config: ✅ PASSED
14. test_e2e_run_history_panel: ✅ PASSED
15. test_e2e_select_historical_run: ✅ PASSED
16. test_e2e_help_icon_visible: ✅ PASSED
```

### Success Criteria

✅ **All tests should PASS:**
- 199 unit tests
- 7 integration tests
- 16 E2E tests
- Total: 222 tests passing

✅ **No failures or errors**

✅ **Coverage > 80%** (for unit tests)

✅ **FRS Coverage: 92%** (24/24 requirements tested)

---

## Integration with GitHub

### Push Test Results to GitHub

```powershell
# 1. Commit Docker files
git add Dockerfile Dockerfile.tests docker-compose.yml .dockerignore DOCKER_*
git commit -m "feat: Add Docker support and comprehensive testing guide"

# 2. Push to GitHub
git push origin master
```

### GitHub Actions CI/CD

Create `.github/workflows/docker-tests.yml`:

```yaml
name: Docker Build and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t qa-agent:test .
      
      - name: Build test image
        run: docker build -f Dockerfile.tests -t qa-agent-tests:test .
      
      - name: Run unit tests
        run: docker run --rm qa-agent-tests:test pytest tests/ -m "not integration" -v
      
      - name: Start app and run E2E tests
        run: |
          docker run -d -p 8501:8501 --name qa-agent qa-agent:test
          sleep 15
          docker run --rm --network host qa-agent-tests:test pytest test_e2e_playwright.py -v
```

---

## Troubleshooting

### Docker Build Issues

**Error:** "Docker daemon is not running"
```powershell
# Solution: Start Docker Desktop
# Or check if WSL2 is properly configured
wsl --list --verbose
```

**Error:** "Failed to resolve 'deb.debian.org'"
```powershell
# Solution: Check internet connection
# May need to configure Docker proxy
```

### Container Issues

**Error:** "Bind for 0.0.0.0:8501 failed: port is already allocated"
```powershell
# Solution 1: Stop conflicting container
docker ps -a
docker stop <container-id>

# Solution 2: Use different port
docker run -p 9000:8501 qa-agent:latest
```

**Error:** "Container exits immediately"
```powershell
# Check logs
docker logs <container-id>

# Common causes:
# 1. Missing OPENAI_API_KEY
# 2. Syntax error in app.py
# 3. Missing dependencies
```

### Test Issues

**Error:** "Connection refused" during E2E tests
```powershell
# Solution: Wait longer for app startup
Start-Sleep -Seconds 30
docker exec qa-agent curl http://localhost:8501
```

**Error:** "Playwright browser not found"
```powershell
# Solution: Reinstall Playwright
docker exec qa-agent-tests playwright install chromium --with-deps
```

**Error:** "OPENAI_API_KEY not set"
```powershell
# Solution: Create .env file with key
echo "OPENAI_API_KEY=sk-..." > .env

# Or pass via environment
docker run --env OPENAI_API_KEY="your-key" ...
```

---

## Summary Checklist

- [ ] Docker and Docker Compose installed
- [ ] `.env` file created with OPENAI_API_KEY
- [ ] Application image built successfully
- [ ] Test image built successfully
- [ ] Application container starts and responds
- [ ] 199 unit tests pass
- [ ] 7 integration tests pass
- [ ] 16 E2E tests pass
- [ ] Total: 222 tests passing
- [ ] Docker files pushed to GitHub
- [ ] CI/CD workflow configured (optional)

---

## Quick Reference Commands

```powershell
# Build
docker build -t qa-agent:latest .
docker build -f Dockerfile.tests -t qa-agent-tests:latest .

# Run app
docker-compose up -d

# Test unit
docker run --rm qa-agent-tests:latest pytest tests/ -m "not integration" -v

# Test integration
docker run --rm --env-file .env qa-agent-tests:latest pytest tests/ -m integration -v

# Test E2E
docker-compose run --rm qa-agent-tests pytest test_e2e_playwright.py -v

# Stop
docker-compose down

# Cleanup
docker system prune -a
```

---

## Next Steps

1. ✅ Follow the step-by-step testing guide above
2. ✅ Verify all tests pass
3. ✅ Push to GitHub with commit message
4. ✅ Set up GitHub Actions for automated testing
5. ✅ Deploy to production (or container registry)

**You now have a fully containerized, tested, and production-ready application!** 🐳🎉
