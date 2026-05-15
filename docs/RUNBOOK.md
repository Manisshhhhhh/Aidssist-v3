# Aidssist V3 Runbook

## Local Startup

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

cd ../web
npm run dev
```

## Docker Startup

```bash
docker compose build
docker compose up -d
docker compose ps
curl -i http://127.0.0.1:8000/health
```

Frontend: <http://127.0.0.1:8080>

## Health And Logs

```bash
curl -i http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/diagnostics/preflight
docker compose logs backend --tail=100
docker compose logs worker --tail=100
```

Use `X-Request-ID` from failed responses to trace backend logs.

## Smoke Tests

```bash
cd backend
.venv/bin/python scripts/smoke_test.py
.venv/bin/python scripts/smoke_test.py --async-jobs
.venv/bin/python scripts/smoke_test.py --preflight
.venv/bin/python scripts/smoke_test.py --backup
```

## Failed Migration Recovery

1. Enable read-only or safe mode.
2. Create a backup.
3. Review `alembic current` and `alembic history`.
4. Fix migration/config.
5. Run `alembic upgrade head`.
6. Run preflight and smoke tests.

If a local development SQLite DB was created before Alembic existed, `alembic upgrade head` may fail with existing-table errors. For disposable local data, recreate the DB. For data you need to keep, create a backup first and only then use an intentional Alembic stamp/migration recovery procedure.

## Stuck Job Recovery

```bash
cd backend
.venv/bin/python scripts/recover_jobs.py
.venv/bin/python scripts/recover_jobs.py --apply
```

Dry run is the default.

## Missing Artifact Recovery

```bash
cd backend
.venv/bin/python scripts/storage_audit.py
.venv/bin/python scripts/repair_artifacts.py
.venv/bin/python scripts/sync_filesystem_to_db.py
```

`repair_artifacts.py` is dry-run by default. Prefer `sync_filesystem_to_db.py` for known historical files.

## Gemini Disabled Or Missing Key

AI summaries are optional and disabled by default. A clean `503` from `/ai-summary` is expected when:

- `AIDSSIST_LLM_ENABLED=false`
- `GEMINI_API_KEY` is missing

Never use keys pasted into chat history.

## Emergency Read-Only Mode

```bash
export AIDSSIST_READ_ONLY_MODE=true
```

Use safe mode for stricter emergency behavior:

```bash
export AIDSSIST_SAFE_MODE=true
```

## Release Checklist

1. Backend tests pass.
2. Frontend typecheck/build pass.
3. Alembic upgrade head passes on a fresh DB.
4. Sync and async smoke pass.
5. Preflight is ok or known warnings are documented.
6. Backup creation and restore validation pass.
7. Storage/job audits are clean or documented.
8. Docker runtime verification passes on a Docker-enabled machine.
