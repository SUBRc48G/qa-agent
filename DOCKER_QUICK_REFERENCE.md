# Docker Quick Reference - QA Agent

Quick reference for common Docker commands for the QA Agent project.

---

## 🚀 Quick Start (Copy & Paste)

### Option 1: Docker Compose (Recommended)

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f qa-agent

# Run tests
docker-compose run --rm qa-agent-tests pytest tests/ -v

# Stop everything
docker-compose down
```

**App URL:** http://localhost:8501

### Option 2: Manual Docker

```bash
# Build
docker build -t qa-agent:latest .

# Run
docker run -d -p 8501:8501 --name qa-agent qa-agent:latest

# View logs
docker logs -f qa-agent

# Stop
docker stop qa-agent
```

---

## 📋 Command Cheat Sheet

### Building

```bash
# Build application image
docker build -t qa-agent:latest .

# Build test image
docker build -f Dockerfile.tests -t qa-agent-tests:latest .

# Build with no cache
docker build --no-cache -t qa-agent:latest .

# Build and view progress
docker build --progress=plain -t qa-agent:latest .
```

### Running

```bash
# Run app (background)
docker run -d -p 8501:8501 --name qa-agent qa-agent:latest

# Run app (foreground with logs)
docker run -p 8501:8501 qa-agent:latest

# Run with volumes
docker run -d -p 8501:8501 \
  -v $(pwd)/outputs:/app/outputs \
  --name qa-agent qa-agent:latest

# Run with environment
docker run -d -p 8501:8501 \
  -e OPENAI_API_KEY="your-key" \
  --name qa-agent qa-agent:latest

# Run with resource limits
docker run -d -p 8501:8501 \
  --cpus="2" --memory="2g" \
  --name qa-agent qa-agent:latest
```

### Logs and Monitoring

```bash
# View logs
docker logs qa-agent

# Follow logs (live)
docker logs -f qa-agent

# Last 100 lines
docker logs --tail=100 qa-agent

# Check stats
docker stats qa-agent

# Check health
docker exec qa-agent curl http://localhost:8501/_stcore/health
```

### Stopping and Cleanup

```bash
# Stop container
docker stop qa-agent

# Remove container
docker rm qa-agent

# Stop and remove
docker stop qa-agent && docker rm qa-agent

# Remove image
docker rmi qa-agent:latest

# Prune unused resources
docker system prune -a
```

### Executing Commands

```bash
# Run command in container
docker exec qa-agent ls -la

# Open shell
docker exec -it qa-agent /bin/bash

# Run tests in container
docker exec qa-agent pytest tests/ -v

# Install package
docker exec qa-agent pip install package-name
```

---

## 🧪 Testing Commands

### Unit Tests

```bash
# In Docker
docker run --rm qa-agent-tests:latest pytest tests/ -v

# Run specific test file
docker run --rm qa-agent-tests:latest pytest tests/test_extract_json_advanced.py -v

# Run with coverage
docker run --rm qa-agent-tests:latest pytest tests/ --cov=. --cov-report=term-missing
```

### Integration Tests

```bash
# Only integration tests
docker run --rm qa-agent-tests:latest pytest -m integration -v

# Only unit tests
docker run --rm qa-agent-tests:latest pytest -m "not integration" -v
```

### E2E Tests

```bash
# Start app first
docker-compose up -d qa-agent

# Run E2E tests
docker-compose run --rm qa-agent-tests pytest test_e2e_playwright.py -v

# Stop app
docker-compose down
```

### All Tests

```bash
# Complete test suite
docker run --rm qa-agent-tests:latest pytest tests/ test_e2e_playwright.py -v --tb=short

# With HTML report
docker run --rm \
  -v $(pwd):/app \
  qa-agent-tests:latest \
  pytest tests/ --html=report.html
```

---

## 🐳 Docker Compose Commands

### Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d qa-agent

# Rebuild and start
docker-compose up -d --build

# View running services
docker-compose ps

# View service logs
docker-compose logs qa-agent

# Follow logs
docker-compose logs -f qa-agent
```

### Execute in Services

```bash
# Run command in service
docker-compose exec qa-agent ls -la

# Open shell in service
docker-compose exec qa-agent bash

# Run tests
docker-compose run --rm qa-agent-tests pytest tests/ -v
```

### Stop and Cleanup

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove with volumes
docker-compose down -v

# Remove images too
docker-compose down --rmi all
```

---

## 📊 Information and Inspection

### Images

```bash
# List images
docker images

# List images with filter
docker images qa-agent

# Inspect image
docker inspect qa-agent:latest

# View image history
docker history qa-agent:latest

# Get image size
docker images --no-trunc -q qa-agent:latest | \
  xargs -I {} docker inspect {} | grep -i size
```

### Containers

```bash
# List running containers
docker ps

# List all containers
docker ps -a

# Inspect container
docker inspect qa-agent

# View container processes
docker top qa-agent
```

### Networks and Volumes

```bash
# List networks
docker network ls

# Inspect network
docker network inspect qa-network

# List volumes
docker volume ls

# Inspect volume
docker volume inspect qa-agent_outputs
```

---

## 🔧 Troubleshooting Commands

```bash
# Check if container is running
docker ps | grep qa-agent

# Check exit code
docker inspect qa-agent --format='{{.State.ExitCode}}'

# View full logs
docker logs qa-agent 2>&1 | tail -50

# Test health
docker exec qa-agent curl -f http://localhost:8501/_stcore/health

# Check resource usage
docker stats --no-stream qa-agent

# Debug: run with interactive shell
docker run -it qa-agent:latest /bin/bash

# Check Python version
docker exec qa-agent python --version

# Check installed packages
docker exec qa-agent pip list

# Check environment
docker exec qa-agent env | grep -i open
```

---

## 🚨 Common Issues and Fixes

### Port Already in Use

```bash
# Find container using port 8501
docker ps -a --filter publish=8501

# Use different port
docker run -d -p 9000:8501 qa-agent:latest

# Or stop conflicting container
docker stop container-name
```

### Container Won't Start

```bash
# Check logs
docker logs qa-agent

# Run interactively to see error
docker run -it qa-agent:latest

# Check image
docker inspect qa-agent:latest
```

### Connection Refused

```bash
# Wait for startup
sleep 15 && curl http://localhost:8501

# Check port is exposed
docker port qa-agent

# Test from inside container
docker exec qa-agent curl http://localhost:8501
```

### Permission Denied

```bash
# Windows: Run as Administrator
# Or run docker commands with sudo (Linux/Mac)

# Check file permissions
docker exec qa-agent ls -la /app
```

### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Full cleanup
docker system prune -a --volumes
```

---

## 📝 Quick Task Reference

| Task | Command |
|------|---------|
| Start app | `docker-compose up -d` |
| Stop app | `docker-compose down` |
| View logs | `docker-compose logs -f qa-agent` |
| Run tests | `docker-compose run --rm qa-agent-tests pytest tests/ -v` |
| Run E2E tests | `docker-compose up -d && docker-compose run --rm qa-agent-tests pytest test_e2e_playwright.py -v` |
| Access shell | `docker-compose exec qa-agent bash` |
| Check health | `docker exec qa-agent curl http://localhost:8501/_stcore/health` |
| View images | `docker images` |
| View containers | `docker ps -a` |
| Clean up all | `docker system prune -a` |

---

## 🎯 Workflow Examples

### Development Workflow

```bash
# 1. Build latest image
docker build -t qa-agent:dev .

# 2. Run container
docker run -d -p 8501:8501 -v $(pwd):/app --name qa-agent qa-agent:dev

# 3. Make changes to code (auto-reload with Streamlit)

# 4. Run tests
docker exec qa-agent pytest tests/ -v

# 5. View logs
docker logs -f qa-agent

# 6. Clean up
docker stop qa-agent && docker rm qa-agent
```

### Testing Workflow

```bash
# 1. Build test image
docker build -f Dockerfile.tests -t qa-agent-tests .

# 2. Run unit tests
docker run --rm qa-agent-tests pytest tests/ -v

# 3. Start app
docker-compose up -d qa-agent

# 4. Run E2E tests
docker-compose run --rm qa-agent-tests pytest test_e2e_playwright.py -v

# 5. Check coverage
docker run --rm qa-agent-tests pytest tests/ --cov --cov-report=html

# 6. Clean up
docker-compose down
```

### Production Workflow

```bash
# 1. Build production image
docker build -t qa-agent:v1.0 .

# 2. Test image
docker run -d -p 8501:8501 --name test-qa-agent qa-agent:v1.0

# 3. Run tests
docker exec test-qa-agent pytest tests/ -v

# 4. Stop test container
docker stop test-qa-agent

# 5. Push to registry
docker tag qa-agent:v1.0 registry/qa-agent:v1.0
docker push registry/qa-agent:v1.0

# 6. Deploy
docker run -d --restart unless-stopped \
  -p 8501:8501 \
  --env-file .env \
  registry/qa-agent:v1.0
```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Documentation](https://docs.docker.com/compose)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder)

---

**Quick Tip:** Bookmark this guide for quick copy-paste commands! 📌
