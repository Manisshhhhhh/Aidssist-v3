# Aidssist V3 RC3

Date: 2026-05-18

Aidssist V3 RC3 is a release-candidate package for local development, Docker Compose demos, and internal evaluation. It is not yet approved for public internet deployment.

## Verified In This Environment

Docker Desktop runtime verification passed on macOS. The following checks were completed:

- Backend test suite: `207 passed`
- Frontend typecheck: passed
- Frontend production build: passed
- Local backend health: passed, including `X-Request-ID` and security headers
- Local sync smoke: passed
- Local async-job smoke: passed
- Docker Compose no-cache build: passed
- Docker Compose startup: passed
- Docker backend health: passed, including `X-Request-ID` and security headers
- Docker frontend nginx and favicon: passed
- Docker sync smoke: passed
- Docker async worker smoke: passed
- Docker restart persistence: passed
- Docker fresh-volume startup: passed
- Docker fresh upload/report smoke: passed
- Job audit script: passed with no queued, running, or failed jobs
- LLM-disabled endpoint behavior: passed with clean `503 Service Unavailable`

Docker storage audit completed with no missing active artifacts. It reported only report `manifest.json` files as orphan storage objects; these are harmless generated metadata files that are not currently registered as artifacts.

## Docker Quick Start

From the repository root:

```bash
docker compose down --remove-orphans
docker compose build --no-cache
docker compose up -d
docker compose ps
curl -i http://127.0.0.1:8000/health
```

Open:

- Frontend: <http://127.0.0.1:8080>
- Backend health: <http://127.0.0.1:8000/health>
- Backend OpenAPI docs: <http://127.0.0.1:8000/docs>

Run the Docker smoke test:

```bash
make docker-smoke
```

For a local release gate, run:

```bash
make release-check
```

This verifies the working tree is clean, runs backend tests, frontend checks, Docker Compose config, Docker build, and Docker smoke when Docker Desktop is available.

## Worker Smoke

Start the worker profile:

```bash
COMPOSE_PROFILES=worker docker compose up -d worker
cd backend
.venv/bin/python scripts/smoke_test.py --base-url http://127.0.0.1:8000 --async-jobs
```

Expected result:

- async analysis job succeeds
- async report job succeeds
- report download succeeds
- no failed worker loop in `docker compose logs worker --tail=100`

## Auth-Enabled Smoke

Use a development-only JWT secret for the smoke pass:

```bash
AIDSSIST_USER_AUTH_ENABLED=true \
AIDSSIST_JWT_SECRET_KEY=dev-only-change-me-long-random-secret \
AIDSSIST_AUTH_ENABLED=false \
docker compose up -d --build
```

Then run:

```bash
cd backend
AIDSSIST_USER_AUTH_ENABLED=true \
  AIDSSIST_JWT_SECRET_KEY=dev-only-change-me-long-random-secret \
  .venv/bin/python scripts/smoke_test.py --base-url http://127.0.0.1:8000
```

Manual browser checks:

- register a user
- log in
- confirm a personal workspace exists
- upload `sample_data/sales_timeseries.csv`
- open dashboard
- generate report
- log out and confirm protected data is not available

## Persistence Test

With Docker running:

1. Upload `sample_data/sales_timeseries.csv`.
2. Generate a report and note the dataset id.
3. Restart containers without deleting volumes:

```bash
docker compose restart
```

4. Refresh <http://127.0.0.1:8080>.
5. Confirm the dataset still appears and report download still works.
6. Stop and start again:

```bash
docker compose down
docker compose up -d
```

7. Confirm persistence again.

## Fresh Install Test

Only after the persistence test passes:

```bash
docker compose down --volumes --remove-orphans
docker compose up -d --build
curl -i http://127.0.0.1:8000/health
```

Expected result:

- clean app starts
- migrations are current
- no old datasets appear
- fresh upload works

## Operational Checks

Run these after Docker smoke:

```bash
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/storage_audit.py
docker compose exec backend python scripts/job_audit.py
docker compose logs backend --tail=100
docker compose logs frontend --tail=100
docker compose logs worker --tail=100
```

Expected:

- Alembic is at head and `upgrade head` is idempotent.
- No missing active artifacts in a fresh Docker volume.
- No stuck running jobs.
- Backend logs do not contain secrets, JWTs, API keys, or raw dataset rows.

## LLM Checks

Default RC behavior:

```bash
curl -i -X POST http://127.0.0.1:8000/datasets/{dataset_id}/ai-summary \
  -H "Content-Type: application/json" \
  -d '{"include_forecast":true,"include_charts":true,"tone":"executive","format":"bullets"}'
```

Expected:

- clean `503 Service Unavailable`
- message says LLM features are disabled
- no key leakage

Optional Gemini-enabled smoke should only use a new rotated key:

```bash
cd backend
AIDSSIST_LLM_ENABLED=true \
  GEMINI_API_KEY=<new-rotated-key> \
  .venv/bin/python scripts/smoke_test.py --llm
```

Never use a key pasted into chat history.

## Known RC Limitations

- No HTTPS termination in Compose.
- SQLite is the default metadata DB.
- Local filesystem storage is the default artifact backend.
- S3 settings are scaffolded but not production-verified.
- User auth has no email verification, password reset, OAuth, MFA, or polished admin UI.
- Background jobs use a database-backed queue, not Redis/Celery.
- Audit logs live in the application DB and are not immutable/WORM storage.
- Gemini summaries are optional, disabled by default, and require a rotated server-side key.

## Rollback Notes

For local Docker demos:

```bash
docker compose down
```

To reset all Docker state:

```bash
docker compose down --volumes --remove-orphans
```

This deletes uploaded datasets, generated reports, the SQLite DB, jobs, and audit records stored in Docker volumes.

For local development, stop the backend/frontend processes and restore from your source-control snapshot or backup.
