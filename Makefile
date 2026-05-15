.PHONY: backend-install backend-test backend-run backend-migrate worker worker-once frontend-install frontend-build frontend-run smoke smoke-async backup restore preflight recover-jobs repair-artifacts fail-safe-check docker-build docker-up docker-down docker-logs docker-smoke

backend-install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

backend-test:
	cd backend && .venv/bin/pytest

backend-run:
	cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app

backend-migrate:
	cd backend && .venv/bin/alembic upgrade head

worker:
	cd backend && .venv/bin/python scripts/worker.py

worker-once:
	cd backend && .venv/bin/python scripts/worker.py --once

frontend-install:
	cd web && npm install

frontend-build:
	cd web && npm run typecheck && npm run build

frontend-run:
	cd web && npm run dev

smoke:
	cd backend && .venv/bin/python scripts/smoke_test.py

smoke-async:
	cd backend && .venv/bin/python scripts/smoke_test.py --async-jobs

backup:
	cd backend && .venv/bin/python scripts/create_backup.py

restore:
	@test -n "$(BACKUP)" || (echo "Usage: make restore BACKUP=path/to/backup.zip" && exit 1)
	cd backend && .venv/bin/python scripts/restore_backup.py "$(BACKUP)" --yes

preflight:
	cd backend && .venv/bin/python -c "from app.db.init_db import init_db; from app.core.preflight import run_preflight; init_db(); print(run_preflight().model_dump_json(indent=2))"

recover-jobs:
	cd backend && .venv/bin/python scripts/recover_jobs.py

repair-artifacts:
	cd backend && .venv/bin/python scripts/repair_artifacts.py

fail-safe-check: preflight recover-jobs repair-artifacts

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-smoke:
	@curl -fsS http://127.0.0.1:8000/health >/dev/null || (echo "Backend is not reachable at http://127.0.0.1:8000. Run 'make docker-up' first." && exit 1)
	cd backend && .venv/bin/python scripts/smoke_test.py --base-url http://127.0.0.1:8000
