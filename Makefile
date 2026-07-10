# ============================================================
# Makefile — Autonomous Business Operations Copilot
# Common development and deployment commands
# ============================================================

.PHONY: help install dev test lint format type-check docker-up docker-down clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Installation ---
install: ## Install production dependencies
	pip install -e .

dev: ## Install with dev dependencies
	pip install -e ".[dev,eval,frontend]"

# --- Testing ---
test: ## Run all tests
	pytest tests/ -v --cov=src --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/unit/ -v -m unit

test-integration: ## Run integration tests (requires Docker services)
	pytest tests/integration/ -v -m integration

test-e2e: ## Run end-to-end tests
	pytest tests/e2e/ -v -m e2e

# --- Code Quality ---
lint: ## Run linter
	ruff check src/ tests/

format: ## Format code
	ruff format src/ tests/

type-check: ## Run type checker
	mypy src/ --strict

quality: lint type-check ## Run all quality checks

# --- Docker ---
docker-up: ## Start all Docker services
	docker compose up -d

docker-down: ## Stop all Docker services
	docker compose down

docker-logs: ## View Docker service logs
	docker compose logs -f

docker-build: ## Build Docker images
	docker compose build

# --- Application ---
api: ## Run FastAPI development server
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

frontend: ## Run Streamlit frontend
	streamlit run frontend/app.py --server.port 8501

# --- Database ---
db-migrate: ## Run database migrations
	alembic upgrade head

db-revision: ## Create new migration
	alembic revision --autogenerate -m "$(msg)"

db-downgrade: ## Rollback last migration
	alembic downgrade -1

# --- Knowledge ---
seed-knowledge: ## Seed knowledge base
	python scripts/seed_knowledge.py

setup-neo4j: ## Initialize Neo4j schema
	python scripts/setup_neo4j.py

# --- Synthetic Data ---
generate-synthetic: ## Generate synthetic test data
	python scripts/generate_synthetic.py

# --- Benchmarks ---
run-benchmarks: ## Run benchmark suite
	python scripts/run_benchmarks.py

# --- Cleanup ---
clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
