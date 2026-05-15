# Development

## Repository Layout

```text
backend/      FastAPI API, deterministic services, pytest suite
web/          React/Vite/TypeScript frontend
datasets/     Local uploaded dataset storage
backend/aidssist.db  Default local SQLite metadata database
sample_data/  Small local CSVs for QA and demos
docs/         Product, API, architecture, and QA docs
```

## Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
```

Run tests:

```bash
cd backend
.venv/bin/pytest
```

Run smoke test after the backend is running:

```bash
cd backend
.venv/bin/python scripts/smoke_test.py
```

Run async smoke after the backend is running:

```bash
cd backend
.venv/bin/python scripts/smoke_test.py --async-jobs
```

Run a background worker:

```bash
cd backend
.venv/bin/python scripts/worker.py
.venv/bin/python scripts/worker.py --once
```

Run database migrations manually:

```bash
cd backend
.venv/bin/alembic upgrade head
```

Create a new migration after model changes:

```bash
cd backend
.venv/bin/alembic revision --autogenerate -m "describe change"
```

Sync existing filesystem artifacts into the metadata database:

```bash
cd backend
.venv/bin/python scripts/sync_filesystem_to_db.py
```

Audit local storage against artifact records:

```bash
cd backend
.venv/bin/python scripts/storage_audit.py
```

## Frontend Setup

```bash
cd web
npm install
npm run dev
```

Run checks:

```bash
cd web
npm run typecheck
npm run build
```

## Environment

Frontend:

- `VITE_API_BASE_URL`: backend URL. Default resolves to the current browser hostname on port `8000`.
- `VITE_AIDSSIST_API_KEY`: optional internal/demo API key sent as `X-Aidssist-API-Key`.

Backend:

- `AIDSSIST_ENVIRONMENT`
- `AIDSSIST_DATABASE_URL`
- `AIDSSIST_MAX_UPLOAD_MB`
- `AIDSSIST_AUTH_ENABLED`
- `AIDSSIST_API_KEY`
- `AIDSSIST_USER_AUTH_ENABLED`
- `AIDSSIST_JWT_SECRET_KEY`
- `AIDSSIST_JWT_ALGORITHM`
- `AIDSSIST_ACCESS_TOKEN_EXPIRE_MINUTES`
- `AIDSSIST_RATE_LIMIT_ENABLED`
- `AIDSSIST_RATE_LIMIT_REQUESTS`
- `AIDSSIST_RATE_LIMIT_WINDOW_SECONDS`
- `AIDSSIST_ASYNC_JOBS_ENABLED`
- `AIDSSIST_JOB_POLL_INTERVAL_SECONDS`
- `AIDSSIST_JOB_MAX_ATTEMPTS`
- `AIDSSIST_JOB_STALE_AFTER_MINUTES`
- `AIDSSIST_STORAGE_BACKEND`
- `AIDSSIST_STORAGE_LOCAL_ROOT`
- `AIDSSIST_REPORTS_LOCAL_ROOT`
- `AIDSSIST_S3_BUCKET`
- `AIDSSIST_S3_REGION`
- `AIDSSIST_S3_ENDPOINT_URL`
- `AIDSSIST_S3_ACCESS_KEY_ID`
- `AIDSSIST_S3_SECRET_ACCESS_KEY`
- `AIDSSIST_S3_PREFIX`
- `AIDSSIST_CORS_ORIGINS`
- `AIDSSIST_CORS_ORIGIN_REGEX`
- `AIDSSIST_DATASETS_DIR`
- `AIDSSIST_REPORTS_DIR`

`VITE_AIDSSIST_API_KEY` is visible in browser builds. Use it only for local/internal demos, not as public-internet authentication.

When `AIDSSIST_USER_AUTH_ENABLED=true`, set `AIDSSIST_JWT_SECRET_KEY` to a strong non-default value. The frontend detects `/auth/status`, shows login/register UI, stores the JWT in localStorage, and sends it as a bearer token.

## Local Data

Structured metadata is stored in SQLite by default:

- `backend/aidssist.db` when commands are run from `backend/`.

PostgreSQL-compatible future URL example:

```text
AIDSSIST_DATABASE_URL=postgresql+psycopg://user:password@host:5432/aidssist
```

Schema migrations are managed with Alembic. Local/demo startup still calls `create_all` as a compatibility safety net, but production-style deployments should run `alembic upgrade head` explicitly before starting or after deploying schema changes.

Raw uploaded and generated files are still stored under `datasets/{dataset_id}/` by default:

- `original.csv`
- `metadata.json`
- `analysis.json`
- `forecast_*.json`
- `reports/{report_id}/report.html`
- `reports/{report_id}/report.json`

Generated local data should not be committed.

## Workspace Roles

When `AIDSSIST_USER_AUTH_ENABLED=true`, users work inside workspaces:

- `owner`: full access, including owner-level membership changes.
- `admin`: dataset actions and member management for editor/viewer users.
- `editor`: upload, analyze, forecast, chat, and generate reports.
- `viewer`: view datasets, chart data, chat, and download existing reports.

New registrations create a personal workspace and owner membership. The frontend stores the selected workspace in localStorage and sends `workspace_id` during upload/list calls.

## Background Jobs

Synchronous endpoint behavior is preserved. Developers can opt into job creation with `?async=true` on analysis, forecast, and report endpoints. Jobs are stored in the database and processed by `scripts/worker.py`.

Current limitations:

- SQLite worker concurrency is limited.
- progress updates are coarse checkpoints.
- cancellation only works before a worker claims the job.
- no Redis/Celery distributed queue yet.

## Storage Artifacts

The local provider stores logical keys under `AIDSSIST_STORAGE_LOCAL_ROOT`. Artifact records track original uploads and generated JSON/HTML outputs. Keep API responses free of local paths; use artifact ids and download endpoints for file access.

S3 settings are present for future implementation, but this local build does not require boto3 or a live bucket.

## Observability

Every backend response includes `X-Request-ID`. Include that value when debugging a failed frontend request. Backend logs include request ids and avoid secrets/raw data.

Useful local diagnostics:

```bash
cd backend
python scripts/job_audit.py
python scripts/storage_audit.py
python scripts/create_backup.py
python scripts/recover_jobs.py
python scripts/repair_artifacts.py
curl http://127.0.0.1:8000/audit/events
curl http://127.0.0.1:8000/diagnostics/system
curl http://127.0.0.1:8000/diagnostics/preflight
```

For auth-enabled mode, diagnostics require a global admin user.

## Fail-Safe Development Checks

Use read-only mode to verify risky writes are blocked without taking down read paths:

```bash
export AIDSSIST_READ_ONLY_MODE=true
```

Use safe mode for emergency startup/runbook checks:

```bash
export AIDSSIST_SAFE_MODE=true
```

Restore is intentionally CLI-only:

```bash
cd backend
python scripts/restore_backup.py backups/aidssist_backup_YYYYMMDD_HHMMSS_xxxxxxxx.zip
```

Run with `--yes` only after stopping the backend and validating the archive.

## Optional Gemini Summaries

LLM features are off by default. To test locally with a newly rotated Gemini key:

```bash
export AIDSSIST_LLM_ENABLED=true
export GEMINI_API_KEY="your-new-rotated-key"
cd backend
python scripts/smoke_test.py --llm
```

Do not paste real keys into source, docs, tests, or chat. Previously exposed keys should be treated as compromised and rotated. The backend uses `google-genai`; do not add legacy `google-generativeai`.

The prompt builder uses deterministic Aidssist outputs only and enforces `AIDSSIST_LLM_MAX_INPUT_CHARS`.

## Development Guidelines

- Keep backend routes thin; put behavior in services.
- Keep frontend API calls typed.
- Do not add LLM behavior until deterministic behavior exists and is covered.
- Do not use user-provided code, SQL, `eval`, `exec`, or shell execution in chat.
- Keep reports grounded in saved metadata, analysis, forecasts, and explicit persisted state.
- Prefer small, targeted tests for new backend behavior.
