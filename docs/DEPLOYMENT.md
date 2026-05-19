# Deployment

Aidssist V3 can run as local development processes or as a Docker Compose deployment. The Docker setup is intended for reliable local demos and internal environments, not a public internet production deployment yet.

For hosted demos on platform-provided URLs, see [Live Deployment](LIVE_DEPLOYMENT.md), [Vercel Deployment](VERCEL_DEPLOYMENT.md), and [Railway Deployment](RAILWAY_DEPLOYMENT.md). You do not need to buy a custom domain for a demo. Vercel or Netlify can host the frontend, but the FastAPI backend must run separately on Render, Railway, Fly.io, or a similar backend host.

If `https://aidssist-v3.onrender.com` shows JSON, that is expected: it is the backend API. Deploy `web/` to Vercel and set `VITE_API_BASE_URL=https://aidssist-v3.onrender.com`; users should open the Vercel URL.

After Vercel deploys, copy the Vercel frontend URL and set this on the Render backend:

```text
AIDSSIST_CORS_ORIGINS=https://<your-vercel-project>.vercel.app
```

Restart or redeploy the Render backend after changing CORS. `AIDSSIST_CORS_ORIGINS=*` is acceptable only as a temporary testing value; use the exact Vercel URL for the final demo.

Generate production secrets locally and paste them only into your hosting provider dashboard:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Use the generated value for `AIDSSIST_JWT_SECRET_KEY` when `AIDSSIST_USER_AUTH_ENABLED=true`. Never commit real secrets.

## Docker Compose Local Deployment

Build images:

```bash
docker compose build
```

Start services:

```bash
docker compose up -d
```

Open:

- Frontend: <http://127.0.0.1:8080>
- Backend: <http://127.0.0.1:8000>
- Health: <http://127.0.0.1:8000/health>

View logs:

```bash
docker compose logs -f
```

Stop services:

```bash
docker compose down
```

## Make Commands

```bash
make docker-build
make docker-up
make docker-logs
make docker-smoke
COMPOSE_PROFILES=worker docker compose up -d worker
make docker-down
```

`make docker-smoke` assumes the backend is reachable at `http://127.0.0.1:8000`.

## Data Persistence

Compose uses named volumes:

- `aidssist_data:/data`

The volume stores:

- SQLite DB: `/data/aidssist.db`
- datasets: `/data/datasets`
- reports and report JSON/HTML artifacts under dataset report folders
- job records in the SQLite DB
- artifact records in the SQLite DB

Reset local Docker data:

```bash
docker compose down -v
```

This deletes the named volumes and all uploaded local Docker data.

## Database

Default local development database:

```text
AIDSSIST_DATABASE_URL=sqlite:///./aidssist.db
```

Docker Compose database:

```text
AIDSSIST_DATABASE_URL=sqlite:////data/aidssist.db
```

PostgreSQL-compatible future example:

```text
AIDSSIST_DATABASE_URL=postgresql+psycopg://user:password@host:5432/aidssist
```

Run migrations before production-style startup:

```bash
docker compose run --rm backend alembic upgrade head
```

For local development:

```bash
cd backend
alembic upgrade head
```

Local/demo startup still calls `create_all` as a compatibility safety net, but migrations are the intended schema path.

Existing filesystem artifacts can be imported with:

```bash
cd backend
python scripts/sync_filesystem_to_db.py
```

## Frontend To Backend URL

Vite environment variables are build-time values. The Compose frontend image is built with:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

That works for local Docker because the browser accesses the backend through the host-published port. If you deploy behind a domain or reverse proxy, rebuild the frontend image with the public backend URL:

```bash
docker compose build --build-arg VITE_API_BASE_URL=https://api.example.com frontend
```

## Internal Demo API Key

Aidssist can require a simple API key for controlled internal demos:

```bash
export AIDSSIST_AUTH_ENABLED=true
export AIDSSIST_API_KEY="replace-with-a-long-random-value"
export VITE_AIDSSIST_API_KEY="$AIDSSIST_API_KEY"
docker compose build frontend
docker compose up -d
```

The frontend key is embedded in the browser bundle. This is only a demo/internal guardrail, not real user authentication. Public deployments need server-side auth, user sessions or tokens, tenant isolation, TLS, and audit logging.

When auth is enabled, avoid wildcard CORS origins. The backend rejects `allow_origins=["*"]` with API-key auth enabled.

## User Auth Mode

User auth is disabled by default so local demos keep working without login. To enable local user accounts and dataset ownership:

```bash
export AIDSSIST_USER_AUTH_ENABLED=true
export AIDSSIST_JWT_SECRET_KEY="replace-with-a-long-random-secret"
docker compose up -d
```

When enabled:

- users register with `/auth/register` and log in with `/auth/login`.
- the frontend stores the JWT access token in localStorage and sends `Authorization: Bearer <token>`.
- new users receive a personal workspace.
- uploads are assigned to the selected workspace.
- normal users only see datasets in workspaces they belong to.
- roles are `owner`, `admin`, `editor`, and `viewer`.
- admin users can access other users' workspaces/datasets, but there is not yet an admin UI.
- ownerless legacy records are hidden from normal users.

This is a foundation for user-owned workspaces, not a complete production identity system. There is no email verification, password reset, OAuth, MFA, email invitations, or full role-management UI yet.

## Upload And Rate Limits

Relevant backend environment variables:

```text
AIDSSIST_MAX_UPLOAD_MB=10
AIDSSIST_RATE_LIMIT_ENABLED=true
AIDSSIST_RATE_LIMIT_REQUESTS=120
AIDSSIST_RATE_LIMIT_WINDOW_SECONDS=60
```

The rate limiter is in-memory and per backend process. It is useful for local/internal demos, but it is not a replacement for edge or Redis-backed limits in multi-replica deployments.

## Background Worker

Async jobs are optional. Existing endpoints stay synchronous unless clients call `?async=true`.

Local worker:

```bash
cd backend
python scripts/worker.py
```

Docker worker profile:

```bash
COMPOSE_PROFILES=worker docker compose up -d worker
```

Useful env vars:

```text
AIDSSIST_ASYNC_JOBS_ENABLED=false
AIDSSIST_JOB_POLL_INTERVAL_SECONDS=2
AIDSSIST_JOB_MAX_ATTEMPTS=3
AIDSSIST_JOB_STALE_AFTER_MINUTES=30
```

The current worker uses the same database and filesystem volumes as the backend. SQLite is acceptable for local demos, but production multi-worker deployments should move to PostgreSQL plus a real queue backend or a carefully managed database-queue strategy.

## Storage Backend

Local storage is the default:

```text
AIDSSIST_STORAGE_BACKEND=local
AIDSSIST_STORAGE_LOCAL_ROOT=/data/datasets
AIDSSIST_REPORTS_LOCAL_ROOT=/data/reports
```

Aidssist stores artifacts with logical object keys and DB artifact records. Report/download endpoints use the storage provider and do not expose local filesystem paths.

S3-compatible variables are scaffolded:

```text
AIDSSIST_S3_BUCKET=
AIDSSIST_S3_REGION=
AIDSSIST_S3_ENDPOINT_URL=
AIDSSIST_S3_ACCESS_KEY_ID=
AIDSSIST_S3_SECRET_ACCESS_KEY=
AIDSSIST_S3_PREFIX=aidssist
```

S3 is not fully implemented or verified in this build. Treat it as a future migration path, not a ready production backend.

## Changing Ports

Edit `docker-compose.yml`:

```yaml
ports:
  - "8080:80"    # frontend host:container
  - "8000:8000" # backend host:container
```

If changing frontend host ports, update backend CORS origins.

## Known Production Limitations

- API-key protection is optional and suitable only for internal demos.
- Local JWT user auth exists, but no email verification, password reset, OAuth, MFA, or role-management UI.
- Workspace permissions exist, but member management is API-first and still needs a polished admin UI.
- SQLite metadata database by default; no managed production database yet.
- Local filesystem still stores uploaded CSV/report artifacts.
- Artifact records track file lifecycle, but retention policies are not implemented.
- No object storage.
- Background jobs use a simple database queue; no Redis/Celery or distributed cancellation yet.
- No HTTPS termination in Compose.
- Rate limiting is in-memory only and not coordinated across replicas.
- No malware scanning for uploaded files.
- Audit logs are stored in the application database and are not immutable.
- No object-storage production verification yet.

## Logs, Audit, And Diagnostics

Docker defaults emit JSON logs and keep audit logging enabled:

```text
AIDSSIST_LOG_LEVEL=INFO
AIDSSIST_LOG_FORMAT=json
AIDSSIST_AUDIT_LOG_ENABLED=true
AIDSSIST_REQUEST_LOGGING_ENABLED=true
AIDSSIST_ERROR_DETAILS_ENABLED=false
AIDSSIST_LLM_ENABLED=false
AIDSSIST_LLM_PROVIDER=gemini
GEMINI_API_KEY=
AIDSSIST_GEMINI_MODEL=gemini-2.5-flash
AIDSSIST_SAFE_MODE=false
AIDSSIST_READ_ONLY_MODE=false
AIDSSIST_BACKUP_DIR=/data/backups
AIDSSIST_STARTUP_PREFLIGHT_ENABLED=true
```

Use request ids from frontend errors or `X-Request-ID` headers to find matching backend log entries. Operational endpoints:

- `GET /diagnostics/system`
- `GET /diagnostics/errors/recent`
- `GET /diagnostics/preflight`
- `GET /audit/events`

Fail-safe commands:

```bash
make preflight
make backup
make recover-jobs
make repair-artifacts
```

For public or regulated production, forward logs to a managed aggregator and move audit retention to immutable storage.

## Optional Gemini Configuration

Gemini summaries are disabled by default. Enable only after privacy/cost review:

```text
AIDSSIST_LLM_ENABLED=true
GEMINI_API_KEY=<new-rotated-key>
AIDSSIST_GEMINI_MODEL=gemini-2.5-flash
```

Never pass provider keys to the frontend. `VITE_` variables are browser-visible and must not contain Gemini keys. Diagnostics only reports whether a key is configured.

## Recommended Next Production Steps

- Put a reverse proxy with TLS in front of frontend/backend.
- Add production-grade authentication, authorization, and role management.
- Move SQLite metadata to managed PostgreSQL.
- Add object storage for uploads and reports.
- Move large analysis/report tasks to a production-grade queue backend when needed.
- Add structured logs, metrics, and traces.
- Add file scanning and stricter upload policies.
- Add backup and retention policies.
