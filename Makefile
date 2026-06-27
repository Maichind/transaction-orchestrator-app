.PHONY: help dev down logs test seed migrate lint

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Docker ─────────────────────────────────────────────────────────────────────
dev: ## Start all services (with hot reload)
	docker compose up --build

down: ## Stop all services
	docker compose down

down-volumes: ## Stop and remove volumes (full reset)
	docker compose down -v

logs: ## Tail logs for all services
	docker compose logs -f

logs-api: ## Tail API logs only
	docker compose logs -f api

logs-worker: ## Tail Celery worker logs
	docker compose logs -f worker

# ── Database ───────────────────────────────────────────────────────────────────
migrate: ## Run Alembic migrations
	docker compose exec api alembic upgrade head

migrate-gen: ## Generate new migration (usage: make migrate-gen MSG="add column")
	docker compose exec api alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed database with demo data
	docker compose exec api python -m scripts.seed

# ── Testing ────────────────────────────────────────────────────────────────────
test: ## Run all tests with coverage
	docker compose exec api pytest tests/ -v --cov=app --cov-report=term-missing

test-unit: ## Run unit tests only
	docker compose exec api pytest tests/unit/ -v

test-integration: ## Run integration tests only
	docker compose exec api pytest tests/integration/ -v

# ── Code quality ───────────────────────────────────────────────────────────────
lint: ## Run ruff linter
	docker compose exec api ruff check app/ tests/

format: ## Auto-format with ruff
	docker compose exec api ruff format app/ tests/
