.PHONY: help build up down restart logs backend-shell db-shell test lint format clean migrate

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker containers
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "✓ Services started!"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - Flower: http://localhost:5555"
	@echo "  - Meilisearch: http://localhost:7700"
	@echo "  - MinIO Console: http://localhost:9001"

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

backend-logs: ## Show backend logs
	docker-compose logs -f backend

worker-logs: ## Show worker logs
	docker-compose logs -f celery-worker

backend-shell: ## Open shell in backend container
	docker-compose exec backend bash

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U seouser -d seosaas

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

test: ## Run tests
	docker-compose exec backend pytest

test-cov: ## Run tests with coverage
	docker-compose exec backend pytest --cov=app --cov-report=html --cov-report=term

lint: ## Run linter (ruff)
	docker-compose exec backend ruff check app/

format: ## Format code with black
	docker-compose exec backend black app/

type-check: ## Run type checker (mypy)
	docker-compose exec backend mypy app/

clean: ## Clean up containers, volumes, and cache
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

migrate: ## Create new migration
	docker-compose exec backend alembic revision --autogenerate -m "$(msg)"

migrate-up: ## Apply migrations
	docker-compose exec backend alembic upgrade head

migrate-down: ## Rollback migration
	docker-compose exec backend alembic downgrade -1

init: ## Initialize project (first time setup)
	@echo "🚀 Initializing SEO SaaS project..."
	@cp backend/.env.example backend/.env || true
	@echo "✓ Environment file created"
	@docker-compose build
	@echo "✓ Containers built"
	@docker-compose up -d postgres redis meilisearch minio
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@docker-compose up -d backend
	@echo "⏳ Waiting for backend..."
	@sleep 5
	@echo "✓ Project initialized!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit backend/.env with your configuration"
	@echo "  2. Run 'make migrate-up' to apply database migrations"
	@echo "  3. Visit http://localhost:8000/docs to see the API"

dev: ## Start development environment
	docker-compose up backend celery-worker flower

status: ## Show service status
	docker-compose ps
