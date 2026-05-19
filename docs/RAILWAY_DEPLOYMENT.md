# Aidssist V3 Railway Deployment

Railway can host Aidssist v3 with platform-provided `.up.railway.app` URLs. Verify current Railway pricing, volume behavior, and free-tier limits before deploying.

Use Railway as the full-stack fallback if a Render backend plus Vercel/Netlify frontend is blocked by service limits, disk limits, or setup complexity. No custom domain is required.

## Suggested Services

Create services from the GitHub repo:

- Backend service from `backend/Dockerfile`.
- Frontend service from `web/Dockerfile` or Railway static build settings.
- Optional worker service from the backend image with command `python scripts/worker.py`.

For a full worker-backed demo, confirm the worker can access the same database and artifacts as the backend. If using SQLite and local storage, do not assume separate services share the same volume unless your Railway setup explicitly provides that behavior. If not, keep jobs synchronous or move to shared managed services.

## Full-Stack Fallback Steps

1. Connect the GitHub repo: `Manisshhhhhh/Aidssist-v3`.
2. Create a backend service using `backend/Dockerfile`.
3. Set the backend start command to:

   ```bash
   ./scripts/start.sh
   ```

4. Add a persistent volume if Railway offers one for your plan. Mount it at `/data`.
5. Configure backend environment variables from the section below.
6. Deploy backend and confirm:

   ```bash
   curl -i https://your-backend-url.up.railway.app/health
   ```

7. Create a frontend service from `web/`, or deploy the frontend to Vercel/Netlify.
8. Set frontend `VITE_API_BASE_URL` to the backend Railway URL.
9. Set backend `AIDSSIST_CORS_ORIGINS` to the frontend URL.
10. Redeploy the frontend after changing `VITE_API_BASE_URL`.
11. Run live smoke from your local machine.

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
