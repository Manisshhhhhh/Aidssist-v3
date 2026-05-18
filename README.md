# Aidssist v3

Status: Release Candidate 1 (`3.0.0-rc1`)

Aidssist v3 is a local-first autonomous data intelligence platform. It uploads CSV and Excel `.xlsx` files, validates and profiles datasets, recommends charts, renders real visualizations, produces deterministic insights, forecasts time series, answers dataset questions with a safe rule-based Q&A engine, and exports HTML/JSON reports.

The product is intentionally deterministic first. LLM explanation layers can be added later behind clean provider interfaces, but analysis, forecasting, chat answers, and reports do not depend on AI-generated guesses.

## Requirements

- macOS, Linux, or Windows with a Unix-like shell for the included Makefile commands.
- Python 3.9+.
- Node.js 20+ and npm 10+ recommended.
- Modern browser: Safari 15+, Chrome, Edge, Firefox, or Arc.

## Security Warning

Aidssist v3 RC1 is suitable for local demos and controlled internal evaluation. It is not ready for public internet deployment without production authentication hardening, TLS, managed database/object storage, backups, monitoring, and operational review.

Never commit real `.env` files, API keys, JWT secrets, databases, uploaded datasets, generated reports, backups, `node_modules`, or Python virtual environments. Gemini keys must stay server-side only; use a newly rotated `GEMINI_API_KEY` and never reuse keys pasted into chat history.

## Quick Start On macOS

From Finder, double-click `start-macos.command`, or run:

```bash
cd ~/Desktop/Aidssist
npm run dev
```

This starts:

- Frontend: <http://127.0.0.1:5173/>
- Backend: <http://127.0.0.1:8000/>
- API docs: <http://127.0.0.1:8000/docs>

Keep the terminal window open while using the app.

`start-macos.command` runs the same dev command for Finder launches.

## Fresh Clone Setup

All-in-one local dev:

```bash
npm run dev
```

The command creates missing local dependencies, starts the backend, reuses an already-running frontend or backend when present, and keeps both services tied to one terminal.

Backend only:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
```

Frontend:

```bash
cd web
npm install
npm run dev
```

Open <http://127.0.0.1:5173/>.

## Docker Quick Start

Docker is the production-style local demo path:

```bash
docker compose down --remove-orphans
docker compose build --no-cache
docker compose up -d
curl -i http://127.0.0.1:8000/health
```

Open <http://127.0.0.1:8080/>.

Run the container smoke test after services are healthy:

```bash
make docker-smoke
```

To start the background worker profile:

```bash
COMPOSE_PROFILES=worker docker compose up -d worker
```

To reset Docker data during a fresh-install test:

```bash
docker compose down --volumes --remove-orphans
```

See [Release Candidate](docs/RELEASE_CANDIDATE.md) for the full RC verification runbook.

## Release Candidate Status

Aidssist V3 RC1 has passed local backend tests, frontend typecheck/build, sync smoke, async-job smoke, and LLM-disabled behavior checks in this workspace. Docker runtime verification still needs to be run on a machine with Docker installed; the exact commands are documented in [Release Candidate](docs/RELEASE_CANDIDATE.md).

## Make Commands

```bash
make backend-install
make backend-migrate
make backend-run
make backend-test
make worker
make worker-once
make frontend-install
make frontend-run
make frontend-build
make smoke
make smoke-async
```

Run `make smoke` after the backend is already running.

## Tests And Builds

Backend:

```bash
cd backend
.venv/bin/pytest
```

Frontend:

```bash
cd web
npm run typecheck
npm run build
```

Backend smoke test:

```bash
cd backend
source .venv/bin/activate
python scripts/smoke_test.py
```

## Sample Data

Use the files in `sample_data/`:

- `sales_timeseries.csv`: charts, forecast, chat, and reports.
- `data_quality_issues.csv`: missing values, duplicates, constant-column insights.
- `no_forecast_dataset.csv`: chart/chat/report flow with forecast empty state.

## Environment Variables

Copy `.env.example` if you need local overrides.

Frontend:

- `VITE_API_BASE_URL`: backend base URL. Defaults dynamically to `http://<current-host>:8000`.
- `VITE_AIDSSIST_API_KEY`: optional internal/demo API key. This is visible in browser builds and is not real user auth.

Backend variables use the `AIDSSIST_` prefix:

- `AIDSSIST_ENVIRONMENT`: environment label.
- `AIDSSIST_DATABASE_URL`: structured metadata DB. Default: `sqlite:///./aidssist.db`.
- `AIDSSIST_MAX_UPLOAD_MB`: upload size limit. Default: `10`.
- `AIDSSIST_AUTH_ENABLED`: require `X-Aidssist-API-Key` on protected endpoints when `true`. Default: `false`.
- `AIDSSIST_API_KEY`: optional internal/demo API key.
- `AIDSSIST_USER_AUTH_ENABLED`: enable real user login/session ownership. Default: `false`.
- `AIDSSIST_JWT_SECRET_KEY`: required strong secret when user auth is enabled.
- `AIDSSIST_JWT_ALGORITHM`: default `HS256`.
- `AIDSSIST_ACCESS_TOKEN_EXPIRE_MINUTES`: default `1440`.
- `AIDSSIST_RATE_LIMIT_ENABLED`: enable in-memory rate limiting. Default: `true`.
- `AIDSSIST_RATE_LIMIT_REQUESTS`: requests per window. Default: `120`.
- `AIDSSIST_RATE_LIMIT_WINDOW_SECONDS`: rate-limit window. Default: `60`.
- `AIDSSIST_ASYNC_JOBS_ENABLED`: enables async-job feature flags for clients. Default: `false`.
- `AIDSSIST_JOB_POLL_INTERVAL_SECONDS`: worker idle sleep interval. Default: `2`.
- `AIDSSIST_JOB_MAX_ATTEMPTS`: max recorded attempts per job. Default: `3`.
- `AIDSSIST_JOB_STALE_AFTER_MINUTES`: future stale-running-job threshold. Default: `30`.
- `AIDSSIST_SAFE_MODE`: emergency safe mode. Default: `false`.
- `AIDSSIST_READ_ONLY_MODE`: read-only maintenance mode. Default: `false`.
- `AIDSSIST_BACKUP_DIR`: local backup zip directory. Default: `./backups`.
- `AIDSSIST_BACKUP_RETENTION_DAYS`: backup age retention. Default: `14`.
- `AIDSSIST_STARTUP_PREFLIGHT_ENABLED`: run startup preflight checks. Default: `true`.
- `AIDSSIST_FAIL_FAST_ON_PREFLIGHT_ERROR`: fail startup on serious preflight errors. Default: `false`.
- `AIDSSIST_AUTO_BACKUP_BEFORE_MIGRATION`: operational flag for migration runbooks. Default: `true`.
- `AIDSSIST_MAX_BACKUP_COUNT`: maximum retained backup zips. Default: `20`.
- `AIDSSIST_STORAGE_BACKEND`: storage provider. Default: `local`.
- `AIDSSIST_STORAGE_LOCAL_ROOT`: local object root. Default: `./datasets`.
- `AIDSSIST_REPORTS_LOCAL_ROOT`: local reports root. Default: `./reports`.
- `AIDSSIST_S3_BUCKET`, `AIDSSIST_S3_REGION`, `AIDSSIST_S3_ENDPOINT_URL`, `AIDSSIST_S3_ACCESS_KEY_ID`, `AIDSSIST_S3_SECRET_ACCESS_KEY`, `AIDSSIST_S3_PREFIX`: future S3-compatible storage settings.
- `AIDSSIST_CORS_ORIGINS`: optional configured frontend origins.
- `AIDSSIST_DATASETS_DIR`: optional local dataset storage directory.
- `AIDSSIST_REPORTS_DIR`: optional local report storage directory.

Default local storage:

- metadata database: `backend/aidssist.db` when running from `backend/`
- datasets: `datasets/`
- generated reports: `datasets/{dataset_id}/reports/{report_id}/`

To import existing filesystem-only dataset artifacts into the database:

```bash
cd backend
python scripts/sync_filesystem_to_db.py
```

Audit storage/artifact lifecycle:

```bash
cd backend
python scripts/storage_audit.py
```

The audit reports missing storage objects, orphaned local files, and soft-deleted artifact records. It never deletes files unless explicitly run with `--delete-orphans --yes`.

Run database migrations explicitly before production-style runs:

```bash
cd backend
alembic upgrade head
```

## User Auth Mode

Local development still works without login by default. To enable user accounts, workspaces, and workspace-level permissions:

```bash
export AIDSSIST_USER_AUTH_ENABLED=true
export AIDSSIST_JWT_SECRET_KEY="replace-with-a-long-random-secret"
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

The frontend detects `/auth/status`, shows login/register UI, stores the JWT in localStorage, and sends `Authorization: Bearer <token>` on API calls. New users get a personal workspace and uploads are assigned to the selected workspace.

Workspace roles:

- `owner`: full workspace control, including owner-level membership changes.
- `admin`: dataset actions and member management for editor/viewer members.
- `editor`: upload, analyze, forecast, chat, and generate reports.
- `viewer`: read datasets, charts, chat, and download existing reports.

## Background Jobs

Heavy endpoints still run synchronously by default. Add `?async=true` to enqueue a durable database-backed job for:

- `POST /datasets/{dataset_id}/analyze`
- `POST /datasets/{dataset_id}/forecast`
- `POST /datasets/{dataset_id}/report`

Run a local worker:

```bash
cd backend
python scripts/worker.py
```

Process one queued job and exit:

```bash
cd backend
python scripts/worker.py --once
```

Check status with `GET /jobs/{job_id}`. SQLite worker concurrency is intentionally modest; Redis/Celery-style distributed queues are future work.

## Observability And Diagnostics

Every backend response includes an `X-Request-ID` header, and frontend API errors include that id when available. Backend logs are structured by default and include request/job/workspace context without logging secrets or uploaded dataset rows.

Audit and diagnostics endpoints:

- `GET /audit/events`
- `GET /audit/events/{audit_id}`
- `GET /diagnostics/system`
- `GET /diagnostics/errors/recent`
- `GET /diagnostics/preflight`
- `POST /backups`
- `GET /backups`
- `GET /backups/{backup_id}/download`

Useful local scripts:

```bash
cd backend
python scripts/job_audit.py
python scripts/storage_audit.py
python scripts/create_backup.py
python scripts/recover_jobs.py
python scripts/repair_artifacts.py
```

Observability env vars:

```text
AIDSSIST_LOG_LEVEL=INFO
AIDSSIST_LOG_FORMAT=json
AIDSSIST_AUDIT_LOG_ENABLED=true
AIDSSIST_REQUEST_LOGGING_ENABLED=true
AIDSSIST_ERROR_DETAILS_ENABLED=false
```

## Optional Gemini AI Summary

Aidssist can generate an optional AI explanation from deterministic analysis outputs. It is disabled by default and uses the current Python `google-genai` SDK when enabled.

```bash
export AIDSSIST_LLM_ENABLED=true
export GEMINI_API_KEY="your-new-rotated-key"
```

Important: do not use keys pasted into chat or committed files. Treat exposed keys as compromised and rotate them. Gemini keys stay server-side only; never put them in `VITE_` frontend variables.

The AI summary does not replace deterministic analysis, forecasting, charts, permissions, storage, jobs, or audit logs. No raw full CSV is sent; prompts are built from bounded metadata, profiles, insights, charts, correlations, and optional forecast summaries.

## Storage And Artifacts

Aidssist uses logical storage keys through a provider abstraction. Local filesystem storage remains the default and maps objects under `AIDSSIST_STORAGE_LOCAL_ROOT`.

The database records durable artifacts for uploaded and generated files:

- original CSV
- metadata JSON
- analysis JSON
- forecast JSON
- report HTML/JSON

S3-compatible storage settings are scaffolded for a future provider, but S3 is not required or fully verified for local development.

## Safari Notes

- Use `http://127.0.0.1:5173/`, not a `file://` URL.
- If Safari shows `API Offline`, wait a moment or click the status badge.
- Favicons are cached aggressively; hard refresh if the app icon looks stale.

## Troubleshooting

- `API Offline`: start the backend and confirm <http://127.0.0.1:8000/health>.
- Upload fails: confirm the file is CSV or Excel `.xlsx` and under 10 MB.
- Forecast unavailable: use a dataset with at least one parseable datetime column and one numeric target.
- Report generation returns 400: open the dashboard first so analysis runs.
- Port already in use: stop the process using port `5173` or `8000`, or edit the run command.
- In some Codex sandbox sessions, `npm` may need a bundled fallback path. Normal local development should use regular `npm`.

## Connector Status

- Excel `.xlsx`: supported through file upload.
- Power BI: connector option is visible, but direct import requires Microsoft OAuth/workspace credentials.
- Tableau: connector option is visible, but direct import requires Tableau REST API credentials.
- Aidssist Link: connector option is visible as a future secure push/import path.

## Documentation

- [Development](docs/DEVELOPMENT.md)
- [API](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [QA Checklist](docs/QA_CHECKLIST.md)
- [Frontend Smoke Test](docs/FRONTEND_SMOKE_TEST.md)
- [Performance Notes](docs/PERFORMANCE.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Production Readiness](docs/PRODUCTION_READINESS.md)
- [Release Candidate](docs/RELEASE_CANDIDATE.md)
- [Release Notes](docs/RELEASE_NOTES.md)
- [GitHub Publication](docs/GITHUB_PUBLICATION.md)
- [Fail-Safe](docs/FAILSAFE.md)
- [Backup And Restore](docs/BACKUP_RESTORE.md)
- [Runbook](docs/RUNBOOK.md)
