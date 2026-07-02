.PHONY: help dev down down-volumes logs logs-api logs-worker \
        migrate migrate-gen seed \
        test test-unit test-integration \
        lint format \
        rpa rpa-install rpa-local

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ─────────────────────────────────────────────────────────────────────
dev: ## Levanta todos los servicios con hot-reload
	docker compose up --build

down: ## Detiene todos los servicios
	docker compose down

down-volumes: ## Detiene y borra volúmenes (reset total)
	docker compose down -v

logs: ## Tail de logs de todos los servicios
	docker compose logs -f

logs-api: ## Tail de logs solo del API
	docker compose logs -f api

logs-worker: ## Tail de logs del Celery worker
	docker compose logs -f worker

# ── Base de datos ──────────────────────────────────────────────────────────────
migrate: ## Ejecuta migraciones Alembic
	docker compose exec api alembic upgrade head

migrate-gen: ## Genera nueva migración (uso: make migrate-gen MSG="add column")
	docker compose exec api alembic revision --autogenerate -m "$(MSG)"

seed: ## Pobla la BD con datos de demo
	docker compose exec api python -m scripts.seed

# ── Tests ──────────────────────────────────────────────────────────────────────
test: ## Corre todos los tests con coverage
	docker compose exec api pytest tests/ -v --cov=app --cov-report=term-missing

test-unit: ## Corre solo tests unitarios
	docker compose exec api pytest tests/unit/ -v

test-integration: ## Corre solo tests de integración
	docker compose exec api pytest tests/integration/ -v

# ── Calidad de código ──────────────────────────────────────────────────────────
lint: ## Linter con ruff
	docker compose exec api ruff check app/ tests/

format: ## Auto-formato con ruff
	docker compose exec api ruff format app/ tests/

# ── RPA ────────────────────────────────────────────────────────────────────────
rpa: ## Corre el scraper via Docker (uso: make rpa TERM="Python language")
	docker compose --profile rpa run --rm rpa $(if $(TERM),$(TERM),FastAPI)

rpa-install: ## Instala dependencias RPA localmente
	cd rpa && pip install -r requirements.txt && playwright install chromium

rpa-local: ## Corre el scraper localmente sin Docker (uso: make rpa-local TERM="FastAPI")
	cd rpa && python wikipedia_scraper.py $(if $(TERM),"$(TERM)","FastAPI")