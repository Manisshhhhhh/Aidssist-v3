# API

Base URL: `http://127.0.0.1:8000`

## Security

By default, local development runs without API-key or user-auth protection. If
`AIDSSIST_AUTH_ENABLED=true`, every endpoint except `/health` requires:

```text
X-Aidssist-API-Key: <your key>
```

Common security errors:

- `401`: API key is missing or invalid.
- `429`: rate limit exceeded.

Browser-provided `VITE_AIDSSIST_API_KEY` is only suitable for internal demos because it is visible to anyone who can inspect the frontend bundle. Public deployments need real user authentication, tenant isolation, TLS, and operational controls.

If `AIDSSIST_USER_AUTH_ENABLED=true`, dataset resources require:

```text
Authorization: Bearer <jwt>
```

New uploads are assigned to the selected workspace. Dataset list/detail, analysis, chart data, forecasts, chat, reports, and report downloads are checked against workspace membership unless the user is marked global admin in the database. Ownerless legacy records are hidden from normal users in auth-enabled mode.

Workspace roles:

- `owner`: full access and owner-level member management.
- `admin`: dataset actions and member management for editor/viewer users.
- `editor`: upload, analyze, forecast, chat, and generate reports.
- `viewer`: view datasets, chart data, chat, and download existing reports.

Structured metadata is stored in the configured database. Raw uploaded CSVs, analysis JSON, forecasts, and report files remain on disk.

## Background Job Responses

Heavy endpoints preserve synchronous behavior by default. Add `?async=true` to enqueue work and receive:

```json
{
  "job_id": "uuid",
  "job_type": "analysis",
  "status": "queued",
  "progress": 0,
  "status_url": "/jobs/{job_id}",
  "created_at": "2026-05-15T10:00:00Z"
}
```

The worker stores the final API response in `output` when the job succeeds.

## GET /auth/status

Purpose: tell the frontend whether user auth and API-key auth are enabled.

Response summary: `user_auth_enabled` and `api_key_auth_enabled`.

## POST /auth/register

Purpose: create a local Aidssist user.

Request shape:

```json
{
  "email": "user@example.com",
  "password": "strong-password",
  "full_name": "User Name"
}
```

Response summary: user id, email, full name, active flag, created timestamp.

Common errors:

- `409`: email already exists.
- `422`: invalid email or password shorter than 8 characters.

## POST /auth/login

Purpose: exchange email/password for a JWT access token.

Request shape:

```json
{
  "email": "user@example.com",
  "password": "strong-password"
}
```

Response summary: bearer token, expiry seconds, and user profile.

Common errors:

- `401`: invalid credentials.
- `403`: inactive account.

## GET /auth/me

Purpose: return the current authenticated user.

Common errors:

- `401`: bearer token is missing, invalid, or expired.

## GET /workspaces

Purpose: list workspaces for the current user. Auth-disabled mode returns the default workspace.

Response summary: workspace id, name, slug, owner id, current user's role, timestamps.

## POST /workspaces

Purpose: create a workspace and add the current user as owner.

Request shape:

```json
{
  "name": "My Workspace"
}
```

Common errors:

- `401`: user auth is enabled and token is missing, or user auth is disabled for create.

## GET /workspaces/{workspace_id}

Purpose: get workspace details.

Common errors:

- `403`: current user is not a member.
- `404`: workspace does not exist.

## GET /workspaces/{workspace_id}/members

Purpose: list workspace members. Requires `admin` or `owner`.

## POST /workspaces/{workspace_id}/members

Purpose: add an existing user to a workspace or update their membership role.

Request shape:

```json
{
  "email": "teammate@example.com",
  "role": "viewer"
}
```

Common errors:

- `400`: user does not exist, role change is invalid, or last-owner rule would be violated.
- `403`: current user cannot manage members.

## PATCH /workspaces/{workspace_id}/members/{user_id}

Purpose: change an existing member role.

Request shape:

```json
{
  "role": "editor"
}
```

## DELETE /workspaces/{workspace_id}/members/{user_id}

Purpose: remove a workspace member. The final owner cannot be removed.

## GET /jobs

Purpose: list visible background jobs.

Optional query:

- `workspace_id=123`
- `status=queued|running|succeeded|failed|cancelled`
- `job_type=analysis|forecast|report|filesystem_sync|future_reserved`
- `limit=50`

Response summary: `{ "jobs": [...] }`.

## GET /jobs/{job_id}

Purpose: return job status, progress, output, and sanitized error message.

Common errors:

- `404`: job does not exist or is not visible to the current user.

## GET /datasets/{dataset_id}/artifacts

Purpose: list stored artifacts for a dataset. Requires dataset `viewer` permission when user auth is enabled.

Response summary: artifact id, type, filename, content type, size, checksum, storage backend, timestamps, and download URL. Raw storage keys and local filesystem paths are not returned.

Common errors:

- `404`: dataset does not exist or is not visible.
- `401`: API key or bearer token required when enabled.

## GET /artifacts/{artifact_id}/download

Purpose: download one stored artifact through the storage provider.

Common errors:

- `404`: artifact does not exist, has been soft-deleted, storage object is missing, or artifact is not visible.
- `401`: API key or bearer token required when enabled.

## POST /jobs/{job_id}/cancel

Purpose: cancel a queued job. Running-job cancellation is not supported yet.

Common errors:

- `400`: job is already running or finished.
- `403`: current user cannot cancel this job.
- `404`: job does not exist or is not visible.

## GET /health

Purpose: check API availability.

Response: status, app name, version, environment.

Common errors: none expected.

## POST /upload

Purpose: upload one CSV or Excel `.xlsx` dataset.

Request: multipart form with `file`.

Optional query:

- `workspace_id=123`: assign upload to a workspace where the current user has `editor` or higher.

Response summary: dataset metadata with `dataset_id`, original filename, file size, row/column counts, and columns. Excel files are converted to the internal `original.csv` format using the first worksheet.

Common errors:

- `400`: missing file, unsupported file type, invalid CSV/Excel.
- `400`: file larger than configured upload limit.
- `401`: API key or bearer token required when enabled.
- `429`: upload rate limit exceeded.

## GET /datasets

Purpose: list uploaded datasets.

Optional query:

- `workspace_id=123`: list datasets in a workspace where the current user has at least `viewer`.

Response summary: array of dataset metadata, including row count, column count, file size, uploaded timestamp, and `last_analyzed_at` when analysis has run.

Common errors:

- `401`: API key or bearer token required when enabled.

## GET /datasets/{dataset_id}

Purpose: get one dataset metadata record.

Response summary: dataset metadata, including row count, column count, file size, uploaded timestamp, columns, and `last_analyzed_at` when analysis has run.

Common errors:

- `404`: dataset does not exist.
- `401`: API key or bearer token required when enabled.

## PATCH /datasets/{dataset_id}

Purpose: rename a dataset display name while preserving stored files and dataset id. Requires dataset `editor` permission when user auth is enabled.

Request shape:

```json
{
  "original_filename": "Q1 sales review"
}
```

Response summary: updated dataset metadata.

Common errors:

- `400`: name is empty or too long.
- `404`: dataset does not exist.
- `401`: API key or bearer token required when enabled.

## DELETE /datasets/{dataset_id}

Purpose: delete one local dataset and its generated artifacts.

Response summary: dataset id, `deleted: true`, and a confirmation message.

Common errors:

- `404`: dataset does not exist.
- `401`: API key or bearer token required when enabled.

## POST /datasets/{dataset_id}/analyze

Purpose: run deterministic profiling, quality scoring, correlations, insights, and chart recommendations.

Response summary: row/column count, column profiles, quality, correlations, insights, recommended charts, created timestamp. Quality includes `quality_score`, missing/duplicate percentages, empty/constant columns, unclear type columns, high-cardinality columns, date parsing issues, outlier columns, and an `issue_breakdown`. With `?async=true`, returns `202` and a job response.

Common errors:

- `404`: dataset does not exist.
- `400`: stored CSV cannot be read.
- `401`: API key or bearer token required when enabled.
- `429`: analysis rate limit exceeded.

## GET /datasets/{dataset_id}/charts/{chart_id}/data

Purpose: generate chart-ready data for a recommended chart.

Optional query:

- `time_range=all`
- `time_range=1d`
- `time_range=1w`
- `time_range=1m`
- `time_range=1q`
- `time_range=1y`
- `time_range=3y`
- `time_range=5y`

Time ranges apply to datetime-based line and area charts and filter to the latest available period.

Response summary: chart metadata and bounded chart data rows.

Common errors:

- `404`: dataset or chart id does not exist.
- `400`: analysis has not been run, chart columns are invalid, or time range is unsupported.
- `401`: API key or bearer token required when enabled.

## POST /datasets/{dataset_id}/forecast

Purpose: create deterministic forecasts for datetime + numeric series.

Request shape:

```json
{
  "date_column": "date",
  "target_column": "sales",
  "periods": 12,
  "frequency": "auto",
  "model": "auto"
}
```

Response summary: historical points, forecast points, metrics, assumptions, warnings, model and frequency used. With `?async=true`, returns `202` and a job response.

Common errors:

- `404`: dataset does not exist.
- `400`: missing columns, invalid dates, non-numeric target, too few valid points.
- `401`: API key or bearer token required when enabled.
- `429`: forecast rate limit exceeded.

## POST /datasets/{dataset_id}/chat

Purpose: safe deterministic dataset Q&A.

Request shape:

```json
{
  "message": "average sales by region",
  "conversation_id": "optional"
}
```

Response summary: answer, intent, confidence, columns used, structured result, follow-up prompts, warnings.

Common errors:

- `404`: dataset does not exist.
- `400`: stored CSV cannot be read.
- `401`: API key or bearer token required when enabled.
- `429`: chat rate limit exceeded.

## POST /datasets/{dataset_id}/ai-summary

Purpose: optional Gemini-powered explanation generated from deterministic Aidssist analysis outputs. It does not send raw full CSV data and does not replace deterministic metrics.

Request shape:

```json
{
  "include_forecast": true,
  "include_charts": true,
  "tone": "executive",
  "format": "bullets"
}
```

Supported `tone`: `executive`, `analyst`, `concise`.
Supported `format`: `bullets`, `narrative`.

Response summary: summary id, provider, model, generated summary, grounding flags, warnings, and created timestamp.

Common errors:

- `400`: analysis has not been run.
- `404`: dataset does not exist.
- `503`: LLM features are disabled or `GEMINI_API_KEY` is not configured.
- `502`: provider failed; error is sanitized.

## POST /datasets/{dataset_id}/report

Purpose: generate an HTML or JSON report after analysis.

Request shape:

```json
{
  "format": "html",
  "include_forecast": true,
  "include_charts": true,
  "include_chat_summary": false,
  "include_ai_summary": false
}
```

Response summary: report id, filename, format, download URL, created timestamp. With `?async=true`, returns `202` and a job response.

Common errors:

- `404`: dataset does not exist.
- `400`: analysis has not been run.
- `401`: API key or bearer token required when enabled.
- `429`: report generation rate limit exceeded.
- `422`: unsupported format.

## GET /datasets/{dataset_id}/reports/{report_id}/download

Purpose: download generated report.

Optional query:

- `format=html`
- `format=json`

Response: `FileResponse` with `text/html` or `application/json`.

Common errors:

- `404`: dataset or report does not exist.
- `401`: API key required when auth is enabled.

## GET /audit/events

Purpose: inspect audit events for debugging and accountability.

Query parameters: `workspace_id`, `dataset_id`, `actor_user_id`, `event_type`, `outcome`, `limit` (default `50`, max `200`), and `offset`.

Response summary: paginated audit events with actor, workspace, dataset, action, outcome, request id, metadata, and timestamp.

Visibility: global admins can see all events; workspace owner/admin users can see workspace events; regular users can see their own actor events. With user auth disabled, local/API-key protected access is allowed.

## GET /audit/events/{audit_id}

Purpose: retrieve one visible audit event.

Common errors: `404` if the event does not exist or is not visible; `401`/`403` when auth or permissions fail.

## GET /diagnostics/system

Purpose: admin operational snapshot with app version, environment, database type, storage backend, feature flags, LLM enabled/provider/model/key-configured status, and aggregate counts. It does not expose secrets, Gemini keys, or full database URLs.

## GET /diagnostics/errors/recent

Purpose: admin troubleshooting view of recent failed jobs and failed audit outcomes.

## GET /diagnostics/preflight

Purpose: run operational preflight checks.

Response summary: overall status (`ok`, `warning`, or `error`) plus checks for database reachability, storage writability, backup directory writability, artifact integrity, stale jobs, LLM/JWT/CORS/rate-limit configuration, and timestamp.

Common errors:

- `401`: auth required when user auth is enabled.
- `403`: admin access required when user auth is enabled.

## POST /backups

Purpose: create a local backup zip.

Request shape:

```json
{
  "include_storage": true,
  "include_reports": true
}
```

Response summary: backup id, filename, size bytes, and created timestamp.

Common errors:

- `401`: auth required when user auth is enabled.
- `403`: admin access required when user auth is enabled.

## GET /backups

Purpose: list local backup zip archives.

## GET /backups/{backup_id}/download

Purpose: download a generated backup zip. The response never exposes absolute local paths.

## Request IDs

Every API response includes `X-Request-ID`. Clients may send a safe `X-Request-ID`; unsafe values are replaced. Error JSON includes `request_id` so frontend support messages can reference backend logs.
