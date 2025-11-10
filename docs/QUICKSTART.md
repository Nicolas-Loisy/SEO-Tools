# Quick Start Guide

## Prerequisites

- Docker & Docker Compose
- Make (optional)
- 4GB+ RAM recommended

## Setup

### 1. Clone and Initialize

```bash
git clone <repository-url>
cd SEO-Tools
make init
```

This will:
- Create `.env` file
- Build Docker containers
- Start core services
- Initialize database

### 2. Bootstrap the Application

```bash
# Start all services
make up

# Wait for services to be ready (30 seconds)
sleep 30

# Run bootstrap script
docker-compose exec backend python /app/scripts/bootstrap.py
```

The bootstrap script will:
- Enable pgvector extension for vector similarity search
- Create database tables
- Create default tenant
- Generate your first API key

**IMPORTANT**: Save the API key displayed - it won't be shown again!

### 3. Verify Installation

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API with your key (replace with your actual key)
curl -H "X-API-Key: sk_test_..." http://localhost:8000/api/v1/auth/me
```

## Create Your First Project

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "name": "My Website",
    "domain": "https://example.com",
    "max_depth": 2,
    "max_pages": 100
  }'
```

### Via Python Script

```python
import requests

API_KEY = "sk_test_..."
BASE_URL = "http://localhost:8000/api/v1"

headers = {"X-API-Key": API_KEY}

# Create project
response = requests.post(
    f"{BASE_URL}/projects/",
    headers=headers,
    json={
        "name": "My Website",
        "domain": "https://example.com",
        "max_depth": 2,
        "max_pages": 100,
    }
)

project = response.json()
print(f"Project created: {project['id']}")
```

## Start Your First Crawl

```bash
# Start crawl
curl -X POST http://localhost:8000/api/v1/crawl/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "project_id": 1,
    "mode": "fast",
    "config": {
      "depth": 2,
      "max_pages": 50
    }
  }'

# Check crawl status (get job_id from response above)
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/v1/crawl/1

# View crawled pages
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/pages/?project_id=1&limit=10"
```

## Run SEO Analysis

### 1. Generate Embeddings

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/v1/analysis/projects/1/embeddings
```

### 2. Compute Link Graph

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/v1/analysis/projects/1/graph
```

### 3. Get Link Recommendations

```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/analysis/projects/1/recommendations?top_k=5"
```

### 4. Find Similar Pages

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/analysis/projects/1/similar-pages/1?limit=10"
```

## Access Services

- **API Documentation**: http://localhost:8000/docs
- **API (Alternative UI)**: http://localhost:8000/redoc
- **Flower (Celery monitoring)**: http://localhost:5555
- **Meilisearch**: http://localhost:7700
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Common Tasks

### View Logs

```bash
make logs                # All services
make backend-logs        # Backend only
make worker-logs         # Celery worker only
```

### Database Access

```bash
make db-shell            # PostgreSQL shell
make redis-cli           # Redis CLI
```

### Run Tests

```bash
make test                # Run all tests
make test-cov            # Run with coverage report
```

### Code Quality

```bash
make format              # Format code with Black
make lint                # Run linter (Ruff)
make type-check          # Run type checker (MyPy)
```

### Stop Services

```bash
make down                # Stop all services
make clean               # Stop and remove volumes
```

## Troubleshooting

### Services won't start

```bash
# Check Docker
docker-compose ps

# Check logs
docker-compose logs backend
docker-compose logs postgres
```

### Database connection errors

```bash
# Restart database
docker-compose restart postgres

# Recreate database
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose up -d backend
```

### "type 'vector' does not exist" error

This error means the pgvector extension is not enabled in PostgreSQL. To fix:

```bash
# Option 1: Recreate database (easiest - loses data!)
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose exec backend python /app/scripts/bootstrap.py

# Option 2: Enable extension manually (preserves data)
docker-compose exec postgres psql -U seouser -d seosaas -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker-compose restart backend

# Option 3: Run bootstrap again (will enable extension)
docker-compose exec backend python /app/scripts/bootstrap.py
```

The init script (`database/init.sql`) automatically creates the pgvector extension on first startup. If you're using an existing database, you'll need to enable it manually.

### Worker not processing tasks

```bash
# Check worker logs
docker-compose logs celery-worker

# Restart worker
docker-compose restart celery-worker

# Monitor with Flower
open http://localhost:5555
```

### Reset Everything

```bash
make clean               # Remove all containers and volumes
make init                # Reinitialize from scratch
```

## Next Steps

- Read the [Architecture Documentation](./ARCHITECTURE.md)
- Check the [API Documentation](./API.md)
- See [Contributing Guide](../CONTRIBUTING.md)
- Review the specification in the README

## Getting Help

- GitHub Issues: [Report bugs or request features]
- API Docs: http://localhost:8000/docs (when running)
- Logs: `make logs` for debugging
