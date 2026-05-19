# Aidssist V3 Railway Deployment

Railway can host Aidssist v3 with platform-provided `.up.railway.app` URLs. Verify current Railway pricing, volume behavior, and free-tier limits before deploying.

## Suggested Services

Create services from the GitHub repo:

- Backend service from `backend/Dockerfile`.
- Frontend service from `web/Dockerfile` or Railway static build settings.
- Optional worker service from the backend image with command `python scripts/worker.py`.

For a full worker-backed demo, confirm the worker can access the same database and artifacts as the backend. If using SQLite and local storage, do not assume separate services share the same volume unless your Railway setup explicitly provides that behavior. If not, keep jobs synchronous or move to shared managed services.

## Backend Environment

Set placeholders in the Railway dashboard only. Do not commit real values.

```text
AIDSSIST_ENVIRONMENT=production
AIDSSIST_DATABASE_URL=sqlite:////data/aidssist.db
AIDSSIST_STORAGE_BACKEND=local
AIDSSIST_STORAGE_LOCAL_ROOT=/data/datasets
AIDSSIST_REPORTS_LOCAL_ROOT=/data/reports
AIDSSIST_DATASETS_DIR=/data/datasets
AIDSSIST_REPORTS_DIR=/data/reports
AIDSSIST_BACKUP_DIR=/data/backups
AIDSSIST_USER_AUTH_ENABLED=true
AIDSSIST_JWT_SECRET_KEY=<generated secret>
AIDSSIST_AUTH_ENABLED=false
AIDSSIST_LLM_ENABLED=false
AIDSSIST_AUDIT_LOG_ENABLED=true
AIDSSIST_STARTUP_PREFLIGHT_ENABLED=true
```

Generate the JWT secret locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Frontend Environment

Set:

```text
VITE_API_BASE_URL=https://your-backend-url.up.railway.app
```

The Vite value is used at build time. If the backend public URL changes, rebuild/redeploy the frontend.

## CORS

Set the backend CORS origin to the frontend Railway URL:

```text
AIDSSIST_CORS_ORIGINS=https://your-frontend-url.up.railway.app
```

## Migrations

The backend hosted start script can run:

```bash
alembic upgrade head
```

before starting Uvicorn. If your Railway service command overrides Docker `CMD`, use:

```bash
./scripts/start.sh
```

## Smoke Test

From your local machine:

```bash
BACKEND_URL=https://your-backend-url.up.railway.app ./scripts/live_smoke.sh
```

For auth-enabled smoke:

```bash
export AIDSSIST_USER_AUTH_ENABLED=true
export AIDSSIST_SMOKE_EMAIL=aidssist-smoke@example.com
export AIDSSIST_SMOKE_PASSWORD=aidssist-smoke-password
BACKEND_URL=https://your-backend-url.up.railway.app ./scripts/live_smoke.sh
```

## Checklist

- [ ] GitHub repo connected.
- [ ] Backend service builds from `backend/Dockerfile`.
- [ ] Frontend service builds from `web/`.
- [ ] Persistent volume configured if using SQLite/local artifacts.
- [ ] Strong JWT secret configured.
- [ ] User auth enabled.
- [ ] LLM disabled unless a reviewed key is configured.
- [ ] Frontend `VITE_API_BASE_URL` points to backend URL.
- [ ] Backend CORS allows frontend URL.
- [ ] `/health` returns 200.
- [ ] Live smoke test passes.

## Production Notes

Railway platform URLs are enough for a demo. A custom domain can be added later.

For production, prefer managed PostgreSQL, object storage, queue-backed workers, external monitoring, and a full security review.
