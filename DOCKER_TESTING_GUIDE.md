# Docker Testing Guide - QA Agent

Complete guide for building, running, and testing the QA Agent application in Docker containers.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Building Docker Images](#building-docker-images)
4. [Running the Application](#running-the-application)
5. [Running Tests](#running-tests)
6. [Docker Compose](#docker-compose)
7. [Testing Strategies](#testing-strategies)
8. [Troubleshooting](#troubleshooting)
9. [CI/CD Integration](#cicd-integration)

---

## Quick Start

### Option 1: Using Docker Compose (Easiest) ⭐

```bash
# Navigate to project directory
cd C:\projects\qa-agent

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f qa-agent

# Stop the application
docker-compose down
```

**Access the app:** http://localhost:8501

### Option 2: Manual Docker Commands

```bash
# Build image
docker build -t qa-agent:latest .

# Run container
docker run -d -p 8501:8501 --name qa-agent qa-agent:latest

# View logs
docker logs -f qa-agent

# Stop container
docker stop qa-agent
```

---

## Prerequisites

### Required Software

```powershell
# Check Docker installation
docker --version
# Expected: Docker version 24.0+

# Check Docker Compose
docker-compose --version
# Expected: Docker Compose version 2.0+
```

### Install Docker (if needed)

**Windows:**
```powershell
# Using Chocolatey
choco install docker-desktop

# Or download from: https://www.docker.com/products/docker-desktop
```

**Verify Installation:**
```powershell
docker run hello-world
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# .env
OPENAI_API_KEY=your-api-key-here
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_LOGGER_LEVEL=info
```

---

## Building Docker Images

### Build Application Image

```powershell
# Build from Dockerfile
docker build -t qa-agent:latest .

# Build with specific tag
docker build -t qa-agent:v1.0 .

# Build with build arguments
docker build --build-arg PYTHON_VERSION=3.12 -t qa-agent:latest .

# View build output
docker build -t qa-agent:latest --progress=plain .
```

### Build Test Image

```powershell
# Build test runner image
docker build -f Dockerfile.tests -t qa-agent-tests:latest .

# Verify image
docker images | grep qa-agent
```

### Image Information

```powershell
# Inspect image
docker inspect qa-agent:latest

# Check image size
docker images qa-agent

# View image layers
docker history qa-agent:latest
```

---

## Running the Application

### 1. Run via Docker (Simple)

```powershell
# Run with default settings
docker run -d \
  -p 8501:8501 \
  --name qa-agent \
  qa-agent:latest

# Wait for startup (5-10 seconds)
Start-Sleep -Seconds 10

# View logs
docker logs qa-agent

# Stop container
docker stop qa-agent

# Remove container
docker rm qa-agent
```

### 2. Run with Volume Mounts

```powershell
# Mount for persistent data
docker run -d \
  -p 8501:8501 \
  -v C:\projects\qa-agent\outputs:/app/outputs \
  -v C:\projects\qa-agent\test_downloads:/app/test_downloads \
  --name qa-agent \
  qa-agent:latest

# Access mounted files from host
Get-ChildItem C:\projects\qa-agent\outputs
```

### 3. Run with Environment Variables

```powershell
# Method 1: Pass via -e flag
docker run -d \
  -p 8501:8501 \
  -e OPENAI_API_KEY="your-key-here" \
  -e STREAMLIT_LOGGER_LEVEL=debug \
  --name qa-agent \
  qa-agent:latest

# Method 2: Load from .env file
docker run -d \
  -p 8501:8501 \
  --env-file .env \
  --name qa-agent \
  qa-agent:latest
```

### 4. Run in Interactive Mode (Debugging)

```powershell
# Run with interactive terminal
docker run -it \
  -p 8501:8501 \
  --name qa-agent-debug \
  qa-agent:latest

# In container: You can see all output
# Press Ctrl+C to stop
```

### 5. Run with Resource Limits

```powershell
# Limit CPU and memory
docker run -d \
  -p 8501:8501 \
  --cpus="2" \
  --memory="2g" \
  --name qa-agent \
  qa-agent:latest

# Check resource usage
docker stats qa-agent
```

### Access the Application

```powershell
# Open in browser
Start-Process "http://localhost:8501"

# Via curl (test connection)
curl http://localhost:8501

# Check health status
curl http://localhost:8501/_stcore/health
```

---

## Running Tests

### 1. Unit Tests in Docker

```powershell
# Build test image
docker build -f Dockerfile.tests -t qa-agent-tests:latest .

# Run unit tests
docker run --rm qa-agent-tests:latest \
  pytest tests/ -v --tb=short

# Run specific test file
docker run --rm qa-agent-tests:latest \
  pytest tests/test_extract_json_advanced.py -v

# Run with coverage report
docker run --rm qa-agent-tests:latest \
  pytest tests/ --cov=. --cov-report=html
```

### 2. E2E Tests with Docker Compose

```powershell
# Start application
docker-compose up -d qa-agent

# Wait for app to be healthy (10 seconds)
Start-Sleep -Seconds 10

# Run E2E tests (from docker)
docker-compose run --rm qa-agent-tests \
  pytest test_e2e_playwright.py -v

# Or run E2E tests from host machine
pytest test_e2e_playwright.py -v -s
```

### 3. Integration Tests

```powershell
# Run only integration tests
docker run --rm qa-agent-tests:latest \
  pytest -m integration -v

# Run only unit tests
docker run --rm qa-agent-tests:latest \
  pytest -m "not integration" -v
```

### 4. Full Test Suite

```powershell
# Run all tests with reporting
docker run --rm \
  -v C:\projects\qa-agent:/app \
  qa-agent-tests:latest \
  pytest tests/ test_e2e_playwright.py \
    -v \
    --tb=short \
    --junit-xml=test-results.xml \
    --html=test-report.html
```

---

## Docker Compose

### Start Services

```powershell
# Start application only
docker-compose up -d

# Start with logs
docker-compose up

# Start application in background
docker-compose up -d qa-agent

# Rebuild images and start
docker-compose up -d --build
```

### View Services

```powershell
# List running services
docker-compose ps

# View service logs
docker-compose logs qa-agent

# View logs in real-time
docker-compose logs -f qa-agent

# View last 100 lines
docker-compose logs --tail=100 qa-agent
```

### Run Commands in Services

```powershell
# Execute command in running container
docker-compose exec qa-agent ls -la

# Open shell in container
docker-compose exec qa-agent /bin/bash

# Run one-off command
docker-compose run --rm qa-agent env
```

### Stop and Clean Up

```powershell
# Stop services (keep containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove volumes too
docker-compose down -v

# Remove images too
docker-compose down --rmi all
```

### Full Testing Workflow with Docker Compose

```powershell
# 1. Start application
docker-compose up -d qa-agent
Write-Host "Waiting for app startup..." 
Start-Sleep -Seconds 15

# 2. Run unit tests
docker-compose run --rm qa-agent-tests pytest tests/ -v

# 3. Run E2E tests
docker-compose run --rm qa-agent-tests pytest test_e2e_playwright.py -v

# 4. View logs
docker-compose logs qa-agent | Select-Object -Last 50

# 5. Clean up
docker-compose down
```

---

## Testing Strategies

### Strategy 1: Local Development + Docker

Best for: Development with docker validation

```powershell
# Run app locally for development
.\.venv312\Scripts\python.exe -m streamlit run .\app.py

# Test locally
pytest tests/ -v

# When ready, test in Docker
docker build -t qa-agent:test .
docker run -d -p 8501:8501 qa-agent:test

# Run E2E tests against Docker
$env:APP_URL = "http://localhost:8501"
pytest test_e2e_playwright.py -v
```

### Strategy 2: Fully Containerized

Best for: CI/CD and production validation

```powershell
# Everything in Docker
docker-compose up -d

# Run all tests
docker-compose run --rm qa-agent-tests pytest tests/ test_e2e_playwright.py -v --tb=short

# Cleanup
docker-compose down -v
```

### Strategy 3: Multi-Stage Testing

Best for: Comprehensive validation

```powershell
# Stage 1: Unit tests only
docker run --rm qa-agent-tests:latest pytest tests/ -m "not integration" -v

# Stage 2: Integration tests
docker run --rm qa-agent-tests:latest pytest tests/ -m integration -v

# Stage 3: Start app and run E2E
docker-compose up -d qa-agent
Start-Sleep -Seconds 10
docker-compose run --rm qa-agent-tests pytest test_e2e_playwright.py -v
docker-compose down
```

### Strategy 4: Parallel Testing

Best for: Speed

```powershell
# Run tests in parallel
docker run --rm qa-agent-tests:latest \
  pytest tests/ -n auto -v

# Build and test simultaneously
$buildJob = Start-Job { docker build -t qa-agent:latest . }
pytest tests/ -v  # Run locally while building
Wait-Job $buildJob
```

---

## Troubleshooting

### Container Won't Start

**Symptom:** Container exits immediately

```powershell
# Check exit code and logs
docker logs qa-agent

# Run interactively to see error
docker run -it qa-agent:latest

# Check image integrity
docker inspect qa-agent:latest
```

**Solutions:**
- Missing OPENAI_API_KEY: Set environment variable
- Port already in use: Change port `-p 9000:8501`
- Insufficient memory: Increase Docker memory allocation

### Connection Refused

**Symptom:** Can't connect to http://localhost:8501

```powershell
# Check if container is running
docker ps | grep qa-agent

# Check port mapping
docker port qa-agent

# Test connection
curl http://localhost:8501 -v

# Check from inside container
docker exec qa-agent curl http://localhost:8501
```

**Solutions:**
- Wait 10-15 seconds for Streamlit startup
- Check firewall settings
- Verify port mapping: `docker run -p 8501:8501 ...`

### Tests Fail in Docker But Pass Locally

```powershell
# Check Python version mismatch
docker run --rm qa-agent-tests:latest python --version

# Check dependencies
docker run --rm qa-agent-tests:latest pip list

# Run with verbose output
docker run --rm qa-agent-tests:latest pytest tests/ -vv -s

# Check environment variables
docker run --rm qa-agent-tests:latest env | grep -i open
```

### Playwright Tests Fail in Docker

```powershell
# Ensure Playwright is installed
docker exec qa-agent-tests playwright install chromium

# Run with debug info
docker run --rm \
  -e DEBUG=pw:api \
  qa-agent-tests:latest \
  pytest test_e2e_playwright.py -vv

# Check browser installation
docker run --rm qa-agent-tests:latest \
  playwright install --with-deps chromium
```

### Volume Permission Issues (Windows)

```powershell
# Grant full permissions
icacls "C:\projects\qa-agent\outputs" /grant:r "%USERNAME%:(F)" /t

# Or use named volumes instead
docker run -d \
  -v qa-agent-outputs:/app/outputs \
  -p 8501:8501 \
  qa-agent:latest

# List named volumes
docker volume ls
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/docker-tests.yml
name: Docker Tests

on: [push, pull_request]

jobs:
  docker-build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Build Docker image
        run: docker build -t qa-agent:test .
      
      - name: Run unit tests in Docker
        run: docker run --rm qa-agent:test pytest tests/ -v
      
      - name: Build test image
        run: docker build -f Dockerfile.tests -t qa-agent-tests:test .
      
      - name: Run integration tests
        run: docker run --rm qa-agent-tests:test pytest tests/ -m integration -v
      
      - name: Start app and run E2E tests
        run: |
          docker run -d -p 8501:8501 --name qa-agent qa-agent:test
          sleep 15
          docker run --rm --network host qa-agent-tests:test pytest test_e2e_playwright.py -v
          docker stop qa-agent
```

### Docker Hub Push

```powershell
# Login to Docker Hub
docker login

# Tag image
docker tag qa-agent:latest subrx/qa-agent:latest
docker tag qa-agent:latest subrx/qa-agent:v1.0

# Push to Docker Hub
docker push subrx/qa-agent:latest
docker push subrx/qa-agent:v1.0

# Pull image (from any machine)
docker pull subrx/qa-agent:latest
```

---

## Performance Tips

### Optimize Image Size

```powershell
# Check image size
docker images qa-agent

# Use .dockerignore to exclude files
cat > .dockerignore << 'EOF'
.venv
.venv312
.pytest_cache
__pycache__
outputs
test_downloads
.git
.gitignore
*.pyc
.env
EOF

# Rebuild for smaller image
docker build -t qa-agent:slim .
```

### Optimize Build Speed

```powershell
# Use layer caching effectively
# Put stable commands first, changing commands last

# Use buildkit for parallel builds
$env:DOCKER_BUILDKIT = "1"
docker build -t qa-agent:latest .

# Check build time
Measure-Command { docker build -t qa-agent:latest . }
```

### Monitor Resource Usage

```powershell
# Real-time stats
docker stats qa-agent

# Check memory usage
docker stats --no-stream qa-agent

# Limit resources
docker run -d \
  --cpus="1.5" \
  --memory="1g" \
  -p 8501:8501 \
  qa-agent:latest
```

---

## Summary

| Task | Command |
|------|---------|
| **Build** | `docker build -t qa-agent:latest .` |
| **Run** | `docker run -d -p 8501:8501 qa-agent:latest` |
| **Test (Unit)** | `docker run --rm qa-agent-tests pytest tests/ -v` |
| **Test (E2E)** | `docker-compose up -d && docker-compose run --rm qa-agent-tests pytest test_e2e_playwright.py -v` |
| **Logs** | `docker logs -f qa-agent` |
| **Stop** | `docker-compose down` |

---

## Next Steps

1. ✅ Build Docker image: `docker build -t qa-agent:latest .`
2. ✅ Run container: `docker-compose up -d`
3. ✅ Access app: http://localhost:8501
4. ✅ Run tests: `docker-compose run --rm qa-agent-tests pytest tests/ -v`
5. ✅ Push to registry: `docker push your-registry/qa-agent:latest`

**Happy containerized testing!** 🐳
