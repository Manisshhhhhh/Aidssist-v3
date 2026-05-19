# Aidssist V3 Live Deployment

Aidssist v3 can be deployed for a live demo without buying a custom domain. Use the platform-provided URLs, such as `.onrender.com`, `.up.railway.app`, `.fly.dev`, `.vercel.app`, or `.netlify.app`.

Recommended starting point: frontend on Vercel or Netlify, backend on Render, user auth enabled, a strong JWT secret, Gemini disabled by default, and persistent storage configured before uploading demo data. Railway is the full-stack fallback if Render service/disk limits get in the way.

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

- Frontend: `https://your-frontend.vercel.app`, `https://your-frontend.netlify.app`, or similar.
- Backend: `https://your-backend.onrender.com`, `https://your-backend.up.railway.app`, or similar.

Then configure:

- `VITE_API_BASE_URL=https://your-backend-url`
- `AIDSSIST_CORS_ORIGINS=https://your-frontend-url`
- `AIDSSIST_ENVIRONMENT=production`
- `AIDSSIST_USER_AUTH_ENABLED=true`
- `AIDSSIST_AUTH_ENABLED=false`
- `AIDSSIST_LLM_ENABLED=false`
- `AIDSSIST_STARTUP_PREFLIGHT_ENABLED=true`
- `AIDSSIST_JWT_SECRET_KEY=<strong generated secret>`

Generate a JWT secret locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Never put real secrets in GitHub. Set them only in the hosting provider dashboard.

GitHub Pages is not enough for Aidssist v3 because the product has a FastAPI backend. GitHub Pages can only host static files. If you use a static frontend host such as Vercel or Netlify, the backend still needs to run separately on Render, Railway, Fly.io, or another API host.

## Vercel Frontend + Render Backend

This is the recommended free or low-cost split for a first no-domain demo.

Important: `https://aidssist-v3.onrender.com` is the backend API, not the website. It is normal for that URL to show JSON API metadata. Deploy `web/` to Vercel and open the Vercel URL for the Aidssist UI.

### Backend On Render

1. In Render, create a new web service from `Manisshhhhhh/Aidssist-v3`.
2. Use Docker with root directory `backend`.
3. Use start command:

   ```bash
   ./scripts/start.sh
   ```

4. Set environment variables:

   ```text
   AIDSSIST_ENVIRONMENT=production
   AIDSSIST_DATABASE_URL=sqlite:////data/aidssist.db
   AIDSSIST_STORAGE_BACKEND=local
   AIDSSIST_STORAGE_LOCAL_ROOT=/data/datasets
   AIDSSIST_REPORTS_LOCAL_ROOT=/data/reports
   AIDSSIST_BACKUP_DIR=/data/backups
   AIDSSIST_USER_AUTH_ENABLED=true
   AIDSSIST_JWT_SECRET_KEY=<generated secret>
   AIDSSIST_AUTH_ENABLED=false
   AIDSSIST_LLM_ENABLED=false
   AIDSSIST_AUDIT_LOG_ENABLED=true
   AIDSSIST_STARTUP_PREFLIGHT_ENABLED=true
   ```

5. If Render offers a persistent disk, mount it at `/data`.
6. If persistent disk requires a paid plan, pause and decide whether this is a temporary demo or whether paid storage is acceptable.
7. Deploy and test:

   ```bash
   curl -i https://your-backend.onrender.com/health
   ```

### Frontend On Vercel

1. In Vercel, import the GitHub repo.
2. Set root directory to `web`.
3. Use:
   - Build command: `npm run build`
   - Output directory: `dist`
4. Set:

   ```text
   VITE_API_BASE_URL=https://your-backend.onrender.com
   ```

5. Deploy the frontend.
6. Copy the Vercel frontend URL.
7. In Render backend env, set:

   ```text
   AIDSSIST_CORS_ORIGINS=https://your-frontend.vercel.app
   ```

8. Redeploy/restart the backend.
9. Open the Vercel URL and confirm API status is online.

See [Vercel Deployment](VERCEL_DEPLOYMENT.md) for the exact frontend settings and smoke command.

## Netlify Frontend + Render Backend

Use this if you prefer Netlify for static hosting.

### Backend On Render

Use the same Render backend steps above.

### Frontend On Netlify

1. In Netlify, create a new site from the GitHub repo.
2. Set base directory to `web`.
3. Use:
   - Build command: `npm run build`
   - Publish directory: `web/dist`
4. Set:

   ```text
   VITE_API_BASE_URL=https://your-backend.onrender.com
   ```

5. Deploy the frontend.
6. Copy the Netlify frontend URL.
7. In Render backend env, set:

   ```text
   AIDSSIST_CORS_ORIGINS=https://your-frontend.netlify.app
   ```

8. Redeploy/restart the backend.
9. Open the Netlify URL and confirm API status is online.

## Render Blueprint

This repo includes `render.yaml` for a practical Render starting point:

- `aidssist-v3-backend`: Docker web service with a persistent disk mounted at `/data`.
- `aidssist-v3-frontend`: static frontend built from `web/`.

The blueprint intentionally does not provision a separate worker because Render disks are not shared between services. Enable a worker only after moving job state and artifacts to shared managed services.

After creating the backend, update the frontend `VITE_API_BASE_URL` to the backend `.onrender.com` URL and redeploy the frontend.

The blueprint can be used for Render-only hosting, but Vercel/Netlify plus Render is often simpler for the frontend because Vite environment variables are configured directly in the frontend host.

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

For Vercel:

```text
AIDSSIST_CORS_ORIGINS=https://<your-vercel-project>.vercel.app
```

Temporary testing-only CORS can be:

```text
AIDSSIST_CORS_ORIGINS=*
```

For the final demo, use the exact Vercel URL instead of `*`.

For early demos, a platform-subdomain regex can be used, but production should use exact allowed origins.

## Pricing And Limits

Verify current platform pricing before deployment. Free tiers can sleep, limit build minutes, limit storage, or restrict persistent disks/workers. Persistent storage often requires a paid plan.

If you deploy without persistent storage, uploaded datasets and generated reports may disappear on restart/redeploy. That is acceptable only for a temporary throwaway demo and should not be called verified persistence.

## Gemini

Keep `AIDSSIST_LLM_ENABLED=false` for the first live demo unless you intentionally configure a newly rotated Gemini key in the backend service environment.

Do not expose `GEMINI_API_KEY` to the frontend. Do not commit it. Do not reuse keys pasted into chat history.

## No Custom Domain Required

You can launch with platform URLs. Add a custom domain later only if needed.

Most platforms provide HTTPS for their subdomains. Confirm the backend and frontend URLs both use HTTPS before sharing the demo.
