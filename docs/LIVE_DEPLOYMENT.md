# Aidssist V3 Live Deployment

Aidssist v3 can be deployed for a live demo without buying a custom domain. Use the platform-provided URLs, such as `.onrender.com`, `.up.railway.app`, `.fly.dev`, `.vercel.app`, or `.netlify.app`.

Recommended starting point: a full-enough demo on Render or Railway with user auth enabled, a strong JWT secret, LLM disabled by default, and persistent storage configured before uploading demo data.

## Deployment Profiles

### A. Demo-Light

Use this when you want the fastest public demo link.

- Frontend: Vercel or Netlify static site.
- Backend: Render or Railway web service.
- Worker: omitted or optional.
- Storage: backend platform disk or volume.
- Good for: showing upload, analysis, charting, forecasting, chat, and report export in a controlled demo.
- Tradeoff: background jobs may be skipped unless you add a worker with shared database/storage.

### B. Full Demo

Use this when you want Aidssist to behave closest to the Docker Compose local setup.

- Backend web service.
- Frontend static or web service.
- Worker service.
- Persistent disk or volume.
- SQLite persisted on attached disk for demo data.
- Auth enabled with a strong `AIDSSIST_JWT_SECRET_KEY`.
- LLM disabled unless a newly rotated Gemini key is deliberately configured.

Important Render note: Render persistent disks are attached to a single service instance and are not shared with other services. For a Render SQLite demo, keep the backend disk-backed and use synchronous flows, or move to managed Postgres/object storage before enabling a separate worker. Render documents this limitation in its persistent disk docs: <https://render.com/docs/disks>.

### C. Production Path

This is not required for the current no-domain demo.

- Managed PostgreSQL.
- Object storage for datasets/reports/artifacts.
- Managed queue or Redis/Celery-style worker backend.
- TLS and reverse proxy controls.
- External monitoring and log aggregation.
- Strong auth lifecycle: password reset, MFA/OAuth, tenant isolation review.
- File scanning and operational retention policies.

## Recommended No-Domain Setup

Use platform-provided URLs:

- Frontend: `https://your-frontend.onrender.com` or similar.
- Backend: `https://your-backend.onrender.com` or similar.

Then configure:

- `VITE_API_BASE_URL=https://your-backend-url`
- `AIDSSIST_CORS_ORIGINS=https://your-frontend-url`
- `AIDSSIST_USER_AUTH_ENABLED=true`
- `AIDSSIST_JWT_SECRET_KEY=<strong generated secret>`

Generate a JWT secret locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Never put real secrets in GitHub. Set them only in the hosting provider dashboard.

## Render Blueprint

This repo includes `render.yaml` for a practical Render starting point:

- `aidssist-v3-backend`: Docker web service with a persistent disk mounted at `/data`.
- `aidssist-v3-frontend`: static frontend built from `web/`.

The blueprint intentionally does not provision a separate worker because Render disks are not shared between services. Enable a worker only after moving job state and artifacts to shared managed services.

After creating the backend, update the frontend `VITE_API_BASE_URL` to the backend `.onrender.com` URL and redeploy the frontend.

## Manual Render Steps

1. Connect the GitHub repo: <https://github.com/Manisshhhhhh/Aidssist-v3>
2. Create a Blueprint from `render.yaml`, or create services manually.
3. Confirm backend env vars:
   - `AIDSSIST_USER_AUTH_ENABLED=true`
   - `AIDSSIST_JWT_SECRET_KEY=<generated secret>`
   - `AIDSSIST_LLM_ENABLED=false`
   - `AIDSSIST_DATABASE_URL=sqlite:////data/aidssist.db`
   - `AIDSSIST_STORAGE_LOCAL_ROOT=/data/datasets`
   - `AIDSSIST_REPORTS_LOCAL_ROOT=/data/reports`
   - `AIDSSIST_BACKUP_DIR=/data/backups`
4. Attach a persistent disk to the backend at `/data`.
5. Deploy the backend and confirm `/health`.
6. Set frontend `VITE_API_BASE_URL` to the backend public URL.
7. Deploy the frontend.
8. Set backend CORS to allow the frontend URL.
9. Register a demo user.
10. Run a smoke test.

## Live Smoke Test

From your local machine:

```bash
BACKEND_URL=https://your-backend-url ./scripts/live_smoke.sh
```

Or directly:

```bash
AIDSSIST_SMOKE_BASE_URL=https://your-backend-url python backend/scripts/smoke_test.py
```

If user auth is enabled, also set:

```bash
export AIDSSIST_USER_AUTH_ENABLED=true
export AIDSSIST_SMOKE_EMAIL=aidssist-smoke@example.com
export AIDSSIST_SMOKE_PASSWORD=aidssist-smoke-password
```

## CORS

For a hosted frontend/backend split, the browser calls the backend from the frontend URL. The backend must allow that origin.

Example:

```text
AIDSSIST_CORS_ORIGINS=https://your-frontend.onrender.com
```

For early demos, a platform-subdomain regex can be used, but production should use exact allowed origins.

## Pricing And Limits

Verify current platform pricing before deployment. Free tiers can sleep, limit build minutes, limit storage, or restrict persistent disks/workers. Persistent storage often requires a paid plan.

## Gemini

Keep `AIDSSIST_LLM_ENABLED=false` for the first live demo unless you intentionally configure a newly rotated Gemini key in the backend service environment.

Do not expose `GEMINI_API_KEY` to the frontend. Do not commit it. Do not reuse keys pasted into chat history.

## No Custom Domain Required

You can launch with platform URLs. Add a custom domain later only if needed.

Most platforms provide HTTPS for their subdomains. Confirm the backend and frontend URLs both use HTTPS before sharing the demo.
