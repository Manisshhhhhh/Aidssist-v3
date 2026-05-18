.DEFAULT_GOAL := help

.PHONY: help install dev test typecheck build doctor release-check \
	backend-install backend-test backend-run backend-migrate worker worker-once \
	frontend-install frontend-build frontend-run smoke smoke-async backup restore \
	preflight recover-jobs repair-artifacts fail-safe-check docker-build docker-up \
	docker-down docker-logs docker-smoke

help: ## Show available Make targets.
	@awk 'BEGIN {FS = ":.*##"; printf "Aidssist V3 targets:\n"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: backend-install frontend-install ## Install backend and frontend dependencies.

dev: ## Start the local backend and frontend development servers.
	npm run dev

test: backend-test ## Run the backend test suite.

typecheck: ## Run frontend TypeScript checks.
	cd web && npm run typecheck

build: frontend-build ## Build/check the frontend production bundle.

doctor: ## Check required local tools, env files, and common ports.
	bash scripts/doctor.sh

release-check: ## Run local release checks; includes Docker smoke when Docker is running.
	bash scripts/release_check.sh

backend-install: ## Create backend venv and install Python dependencies.
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

backend-test: ## Run backend pytest.
	cd backend && .venv/bin/pytest

backend-run: ## Run the FastAPI backend locally.
	cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app

backend-migrate: ## Apply backend Alembic migrations.
	cd backend && .venv/bin/alembic upgrade head

worker: ## Run the local background worker loop.
	cd backend && .venv/bin/python scripts/worker.py

worker-once: ## Process one queued background job locally.
	cd backend && .venv/bin/python scripts/worker.py --once

frontend-install: ## Install frontend dependencies.
	cd web && npm install

frontend-build: ## Run frontend typecheck and production build.
	cd web && npm run typecheck && npm run build

frontend-run: ## Run the Vite frontend locally.
	cd web && npm run dev

smoke: ## Run backend smoke test against a running local backend.
	cd backend && .venv/bin/python scripts/smoke_test.py

smoke-async: ## Run async-job smoke test against a running local backend.
	cd backend && .venv/bin/python scripts/smoke_test.py --async-jobs

backup: ## Create a local backup archive.
	cd backend && .venv/bin/python scripts/create_backup.py

restore: ## Restore from backup. Usage: make restore BACKUP=path/to/backup.zip
	@test -n "$(BACKUP)" || (echo "Usage: make restore BACKUP=path/to/backup.zip" && exit 1)
	cd backend && .venv/bin/python scripts/restore_backup.py "$(BACKUP)" --yes

preflight: ## Run backend preflight checks locally.
	cd backend && .venv/bin/python -c "from app.db.init_db import init_db; from app.core.preflight import run_preflight; init_db(); print(run_preflight().model_dump_json(indent=2))"

recover-jobs: ## Dry-run stuck job recovery.
	cd backend && .venv/bin/python scripts/recover_jobs.py

repair-artifacts: ## Dry-run artifact repair.
	cd backend && .venv/bin/python scripts/repair_artifacts.py

fail-safe-check: preflight recover-jobs repair-artifacts ## Run fail-safe diagnostic scripts.

docker-build: ## Build Docker images.
	docker compose build

docker-up: ## Start Docker Compose services.
	docker compose up -d

docker-down: ## Stop Docker Compose services.
	docker compose down

docker-logs: ## Follow Docker Compose logs.
	docker compose logs -f

docker-smoke: ## Run smoke test against a running Docker backend.
	@curl -fsS http://127.0.0.1:8000/health >/dev/null || (echo "Backend is not reachable at http://127.0.0.1:8000. Run 'make docker-up' first." && exit 1)
	cd backend && .venv/bin/python scripts/smoke_test.py --base-url http://127.0.0.1:8000
