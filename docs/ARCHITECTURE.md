# Architecture

## Backend

The backend is a FastAPI application organized by API route, Pydantic model, and service.

- `api/`: thin HTTP route handlers.
- `models/`: request/response schemas.
- `services/`: storage, dataset, analysis, charts, forecasting, chat, reports.
- `repositories/`: SQLAlchemy persistence for structured metadata.
- `db/`: engine/session setup, table models, and startup initialization.
- `core/auth.py` and `core/user_auth.py`: password hashing, JWT creation/validation, and current-user dependencies.
- `core/permissions.py`: workspace and dataset permission dependencies.
- `core/`: settings, paths, shared errors.
- `alembic/`: schema migrations for production-style database evolution.
- `scripts/worker.py`: database-backed background worker.
- `storage/`: logical storage provider abstraction.
- `tests/`: pytest coverage for contracts and behavior.

Services are intentionally deterministic:

- profiling uses pandas.
- chart recommendations use rules.
- chart data is generated from the original CSV.
- forecasting uses linear regression or moving average baselines.
- chat uses intent and column-matching rules.
- reports use saved metadata, analysis, forecast files, and explicit persisted state.

## Frontend

The frontend is a React/Vite/TypeScript app.

- `api/`: typed API clients.
- `types/`: API response contracts.
- `components/`: layout, upload, dashboard, charts, forecast, chat, report, brand, 3D.
- `workspace/`: selected workspace state and localStorage persistence.
- `pages/`: upload flow and dashboard.
- `index.css`: design tokens, global styles, motion/fallback utilities.

The dashboard is state-driven rather than router-driven for now:

1. Upload or select a dataset.
2. Dashboard runs analysis.
3. Charts request chart data by recommendation id.
4. Forecasts run only after user selection.
5. Chat sends safe natural-language prompts to the deterministic backend.
6. Reports are generated after analysis.
7. Optional background jobs can poll `/jobs/{job_id}` for long-running deliverables.

## Data Flow

```text
CSV/Excel upload
  -> datasets/{dataset_id}/original.csv
  -> metadata.json
  -> DB DatasetRecord in selected Workspace
  -> DB ArtifactRecord entries for original/metadata
  -> workspace membership permission checks
  -> owner_user_id retained for compatibility
  -> analysis.json
  -> DB AnalysisRecord
  -> DB ArtifactRecord for analysis JSON
  -> chart-data endpoint
  -> forecast_*.json
  -> DB ForecastRecord
  -> DB ArtifactRecord for forecast JSON
  -> chat answers
  -> DB chat conversation/message records
  -> reports/{report_id}/report.html + report.json
  -> DB ReportRecord
  -> DB ArtifactRecords for report HTML/JSON
  -> optional DB JobRecord for async analysis/forecast/report
```

## Storage Model

Aidssist now uses two persistence layers:

Database:

- SQLite by default through `AIDSSIST_DATABASE_URL=sqlite:///./aidssist.db`.
- Stores workspaces, dataset metadata, analysis summaries, forecast records, report records, and chat exchanges.
- Stores local users with password hashes and dataset owner IDs.
- Stores workspaces and workspace members with `owner`, `admin`, `editor`, and `viewer` roles.
- Stores background jobs with status, progress, sanitized errors, and final output payloads.
- Stores artifact records for upload/generated file lifecycle tracking.
- Creates a default workspace with slug `default` when user auth is disabled.
- Creates a personal workspace for each registered user when user auth is enabled.
- Uses SQLAlchemy models that remain PostgreSQL-compatible where practical.
- Uses Alembic migrations for production-style schema management.

Filesystem:

- each dataset owns its own directory under `datasets/{dataset_id}/`.
- `original.csv` remains the canonical uploaded-data artifact.
- `metadata.json`, `analysis.json`, `forecast_*.json`, and report files remain available for cache/export/backward compatibility.
- Local storage is accessed through logical object keys to prepare for object storage.

Storage can be relocated with:

- `AIDSSIST_DATABASE_URL`
- `AIDSSIST_DATASETS_DIR`
- `AIDSSIST_REPORTS_DIR`

Existing filesystem artifacts can be imported into the DB with:

```bash
cd backend
python scripts/sync_filesystem_to_db.py
```

Storage lifecycle can be audited with:

```bash
cd backend
python scripts/storage_audit.py
```

The S3 provider is scaffolded for future work. Local storage is the only fully implemented provider in this build.

## Why Deterministic First

Aidssist V3 is building trust around data work. The first version must calculate, aggregate, profile, forecast, and answer questions using transparent logic before any LLM is allowed to explain or summarize. This prevents fake insight generation and keeps tests meaningful.

## Workspace Permission Model

Permission checks are workspace-first when `AIDSSIST_USER_AUTH_ENABLED=true`:

- `viewer+`: list/view workspace datasets, chart data, chat, report download.
- `editor+`: upload, analyze, forecast, and generate reports.
- `admin+`: manage editor/viewer members.
- `owner`: owner-level changes and last-owner protection.

Global `is_admin` users can bypass workspace membership checks for support/admin scenarios. API-key auth remains a separate internal/demo guardrail and does not replace user authorization.

## Background Job Model

Aidssist uses a simple database-backed queue for heavier local workloads:

- sync behavior remains the default for existing clients.
- `?async=true` on analysis, forecast, or report endpoints creates a `JobRecord`.
- `scripts/worker.py` claims queued jobs and calls the existing deterministic services.
- `/jobs/{job_id}` exposes status, progress, output, and sanitized errors.
- cancellation is supported for queued jobs only.

The queue is intentionally simple and local-first. SQLite concurrency is limited, and this is not a distributed queue. Redis/Celery or a managed job backend can replace this layer later without changing the analytics services.

## Observability And Audit Model

Aidssist attaches a request id to every HTTP request and emits structured logs with request, user, workspace, dataset, and job context where available. Logs avoid request bodies, uploaded file contents, tokens, API keys, passwords, and raw dataset rows.

Audit logs are stored in the application database for important product and security actions: auth, upload, analysis, forecast, chat, report generation/download, artifact download, job lifecycle, workspace membership changes, unauthorized access, and rate limiting.

Diagnostics endpoints expose operational state without secrets. External log aggregation, metrics, traces, SIEM integration, and immutable audit retention remain future production work.

## Fail-Safe And Recovery

Aidssist has an operational safety layer:

- startup preflight checks database, storage, backup directory, artifacts, stale jobs, and sensitive config.
- read-only/safe mode middleware blocks risky write actions while preserving health, diagnostics, reads, and downloads.
- backup service creates zip archives with the SQLite DB, local storage, reports, and a manifest.
- restore remains CLI-only to avoid dangerous web-triggered data replacement.
- recovery scripts inspect stale jobs and artifact drift without mutating by default.

## Optional LLM Explanation Layer

Aidssist’s Gemini integration is optional and disabled by default. Deterministic analysis, chart recommendations, forecasting, chat rules, permissions, storage, jobs, and audit behavior remain the source of truth.

The LLM layer receives a bounded prompt built from saved metadata, `analysis.json`, quality metrics, deterministic insights, chart recommendations, correlations, and optional forecast summaries. It does not send raw full CSV files, local filesystem paths, API keys, JWTs, or secrets. Generated summaries are stored as `ai_summary_json` artifacts and audited with provider/model and character counts, not prompt bodies.

The provider interface lives under `backend/app/llm/`; the first implementation uses the current `google-genai` SDK for Gemini.

## Current Limitations

- CSV and Excel `.xlsx` upload are supported; Excel uses the first worksheet and is converted to canonical CSV.
- Power BI, Tableau, and Aidssist Link are UI connector targets only until credentials/API flows are configured.
- SQLite stores structured metadata by default, while raw datasets/reports still use local filesystem storage.
- Local email/password JWT auth is available when `AIDSSIST_USER_AUTH_ENABLED=true`.
- No email verification, password reset, OAuth, MFA, or role-management UI yet.
- Workspace permissions are enforced in the API, but the frontend currently exposes only workspace switching and creation; member management is API-only.
- Background progress is coarse and cancellation only applies to queued jobs.
- S3-compatible object storage is scaffolded but not fully implemented or production-verified.
- No lifecycle retention policy or encryption-at-rest controls beyond the underlying platform.
- Audit logs are stored in the app database and are not immutable.
- No external metrics, tracing, SIEM, or OpenTelemetry integration yet.
- Gemini summaries are optional, can incur provider cost, and require privacy/security review before sensitive-data use.
- Chat history is persisted locally in the database and guarded by dataset workspace permissions.
- Reports do not embed chart images.
- PDF export is not implemented; HTML reports can be printed to PDF by the browser.
- Forecasting models are simple baselines, not full seasonal modeling.

## Extension Points

- LLM explanation provider behind a clean interface.
- richer workspace sharing and ownership-transfer UI.
- cloud object storage.
- cloud deployment.
- PDF export.
- project-level organization inside workspaces.
- richer forecasting models.
- distributed queue backend for multi-worker production deployments.
