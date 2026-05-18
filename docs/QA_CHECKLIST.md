# QA Checklist

## Automated

- [ ] Workstation doctor passes: `make doctor`
- [ ] Backend tests pass: `cd backend && .venv/bin/pytest`
- [ ] Frontend typecheck passes: `cd web && npm run typecheck`
- [ ] Frontend build passes: `cd web && npm run build`
- [ ] Release check passes from a clean tree: `make release-check`
- [ ] Backend smoke passes: `cd backend && .venv/bin/python scripts/smoke_test.py`
- [ ] Alembic migration succeeds: `cd backend && .venv/bin/alembic upgrade head`
- [ ] Async smoke passes: `cd backend && .venv/bin/python scripts/smoke_test.py --async-jobs`
- [ ] Storage audit runs: `cd backend && .venv/bin/python scripts/storage_audit.py`
- [ ] Preflight endpoint passes or warnings are documented: `cd backend && .venv/bin/python scripts/smoke_test.py --preflight`
- [ ] Backup smoke passes: `cd backend && .venv/bin/python scripts/smoke_test.py --backup`
- [ ] Backup script works: `cd backend && .venv/bin/python scripts/create_backup.py`
- [ ] Restore script validates a known-good backup in dry-run mode.
- [ ] Recover jobs dry run works: `cd backend && .venv/bin/python scripts/recover_jobs.py`
- [ ] Repair artifacts dry run works: `cd backend && .venv/bin/python scripts/repair_artifacts.py`

## Fail-Safe And Recovery

- [ ] Read-only mode blocks upload.
- [ ] Read-only mode allows health.
- [ ] Read-only mode allows dataset listing.
- [ ] Safe mode blocks risky POST endpoints.
- [ ] `/diagnostics/preflight` checks DB, storage, backup dir, artifacts, jobs, JWT, CORS, rate limit, and LLM config.
- [ ] Backup zip contains `manifest.json`.
- [ ] Backup zip excludes `.env` files.
- [ ] Backup zip excludes previous backup zips.
- [ ] Backup list and download endpoints work.
- [ ] Backup APIs are admin-only when user auth is enabled.
- [ ] Restore script rejects path traversal zip entries.
- [ ] Restore script refuses to run while backend appears active unless `--force` is used.

## Docker Release Candidate

- [x] Docker CLI is installed and reachable: `docker --version`
- [x] Docker build succeeds: `docker compose build --no-cache`
- [x] Docker services start: `docker compose up -d`
- [x] Compose services are healthy: `docker compose ps`
- [x] Backend health returns 200: `curl -i http://127.0.0.1:8000/health`
- [x] Health response includes `X-Request-ID` and security headers.
- [x] Frontend nginx responds: `curl -I http://127.0.0.1:8080`
- [x] Favicon responds: `curl -I http://127.0.0.1:8080/favicon.svg`
- [x] Frontend opens at `http://127.0.0.1:8080`.
- [ ] API status is online in the browser.
- [x] `make docker-smoke` passes.
- [ ] Auth-disabled browser smoke passes.
- [ ] Auth-enabled browser smoke passes.
- [x] Async worker profile starts: `COMPOSE_PROFILES=worker docker compose up -d worker`
- [x] Async worker smoke passes.
- [x] Dataset/report persistence survives `docker compose restart`.
- [ ] Dataset/report persistence survives `docker compose down && docker compose up -d`.
- [x] Fresh install after `docker compose down --volumes --remove-orphans` works.
- [x] Docker storage audit has no missing active artifacts in a fresh volume.
- [x] Docker job audit has no stuck running jobs.
- [ ] LLM-disabled `/ai-summary` returns a clean 503.
- [ ] Optional Gemini-enabled smoke passes only with a new rotated server-side key.

## Upload And Datasets

- [ ] Valid CSV uploads.
- [ ] Non-CSV file is rejected.
- [ ] Invalid CSV content is rejected.
- [ ] Dataset list refreshes after upload.
- [ ] Dataset detail opens from the list.
- [ ] Auth-enabled upload assigns the dataset to the selected workspace.

## Workspaces

- [ ] Registering a user creates a personal workspace.
- [ ] Workspace switcher lists the user's workspaces.
- [ ] Creating a workspace selects it.
- [ ] Viewer members can view datasets but cannot run write actions.
- [ ] Editor members can upload/analyze/forecast/report.
- [ ] Non-members cannot access workspace datasets.

## Analysis Dashboard

- [ ] Overview cards render.
- [ ] Data quality panel renders.
- [ ] Insight list renders.
- [ ] Column profile table does not break mobile width.
- [ ] Correlations render or show a clean empty state.

## Charts

- [ ] Recommended charts appear.
- [ ] Real chart data loads.
- [ ] Tooltips work.
- [ ] Chart failures do not break the dashboard.

## Forecast

- [ ] `sample_data/sales_timeseries.csv` can forecast `sales` by `date`.
- [ ] Metrics, assumptions, and warnings render.
- [ ] `sample_data/no_forecast_dataset.csv` shows forecast unavailable state.

## Chat

- [ ] Ask `summarize this dataset`.
- [ ] Ask `what columns are available?`.
- [ ] Ask `average sales by region` on the sales sample.
- [ ] Ask `what charts should I use?`.
- [ ] Code-like prompts are not executed.

## Reports

- [ ] HTML report generates and opens.
- [ ] JSON report generates and opens.
- [ ] Missing forecast is described cleanly.
- [ ] Existing forecast summary appears when available.
- [ ] Background report job completes and exposes the report download.

## Background Jobs

- [ ] `POST /datasets/{dataset_id}/analyze?async=true` returns a queued job.
- [ ] `python backend/scripts/worker.py --once` processes one queued job.
- [ ] `GET /jobs/{job_id}` returns status and output.
- [ ] Queued jobs can be cancelled.
- [ ] Running jobs return a clean unsupported cancellation message.

## Storage And Artifacts

- [ ] Upload creates original CSV and metadata artifacts.
- [ ] Analysis creates analysis JSON artifact.
- [ ] Forecast creates forecast JSON artifact.
- [ ] Report creates HTML and JSON artifacts.
- [ ] Dataset artifacts endpoint hides storage keys.
- [ ] Artifact download works for authorized users.
- [ ] Non-members cannot list/download workspace artifacts.
- [ ] Storage audit reports missing/orphaned objects without deleting by default.

## Observability And Audit

- [ ] API responses include `X-Request-ID`.
- [ ] Frontend errors show a request id when the backend provides one.
- [ ] Register/login create audit events.
- [ ] Upload/analyze/forecast/chat/report create audit events.
- [ ] Report/artifact downloads create audit events.
- [ ] Job create/succeed/fail/cancel create audit events.
- [ ] Workspace member changes create audit events.
- [ ] `/audit/events` enforces workspace/admin visibility.
- [ ] `/diagnostics/system` is admin-only when user auth is enabled.
- [ ] Backend logs do not include passwords, API keys, JWTs, or raw dataset rows.

## Optional AI Summary

- [ ] AI summary endpoint returns 503 when LLM is disabled.
- [ ] AI summary requires analysis first.
- [ ] AI summary succeeds with a mocked provider in tests.
- [ ] Prompt builder does not send raw full CSV rows.
- [ ] Report can include an AI summary note or generated summary.
- [ ] Gemini keys are never exposed to the frontend or diagnostics.

## UI And Accessibility

- [ ] Theme toggle persists.
- [ ] Reduced-motion fallback works.
- [ ] Upload can be used by keyboard.
- [ ] Dataset selection can be used by keyboard.
- [ ] Forecast controls have labels.
- [ ] Chat input supports Enter and Shift+Enter.
- [ ] Report options can be toggled by keyboard.
- [ ] API offline state is readable.
- [ ] Mobile width remains usable.

## Sample Datasets

- [ ] `sample_data/sales_timeseries.csv`
- [ ] `sample_data/data_quality_issues.csv`
- [ ] `sample_data/no_forecast_dataset.csv`
