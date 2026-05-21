# Aidssist V3 Vercel Frontend Deployment

The Render URL `https://aidssist-v3.onrender.com` is the FastAPI backend. It is expected to show backend API metadata at `/`.

Users should open the Vercel URL after the React frontend is deployed. Aidssist needs both URLs:

- Backend API: `https://aidssist-v3.onrender.com`
- Frontend website: `https://<project-name>.vercel.app`

## Vercel Project Settings

Import this GitHub repository:

```text
Manisshhhhhh/Aidssist-v3
```

Use these settings:

```text
Root Directory: web
Framework Preset: Vite
Install Command: npm install
Build Command: npm run build
Output Directory: dist
```

Environment variable:

```text
VITE_API_BASE_URL=/api
```

`web/vercel.json` rewrites `/api/*` to `https://aidssist-v3.onrender.com/*`. That keeps browser requests on the Vercel origin and prevents API status failures caused by CORS or Vercel preview alias drift.

Do not add backend secrets to Vercel. `AIDSSIST_JWT_SECRET_KEY`, Gemini keys, API keys, databases, reports, datasets, and backups belong only on the backend host or local machine.

## Deploy

1. Open <https://vercel.com/new>.
2. Import `Manisshhhhhh/Aidssist-v3`.
3. Set root directory to `web`.
4. Confirm Framework Preset is `Vite`.
5. Confirm build/output settings.
6. Add `VITE_API_BASE_URL=/api`.
7. Deploy.
8. Copy the generated Vercel URL.

## Render CORS

After Vercel deploys, copy the Vercel frontend URL.

The `/api` proxy means the Vercel demo does not depend on browser CORS for normal use. Keep the exact Vercel URL in Render anyway so direct diagnostics and non-proxied deployments continue to work:

```text
AIDSSIST_CORS_ORIGINS=https://aidssist-v3.vercel.app
AIDSSIST_CORS_ORIGIN_REGEX=^$
```

Then restart or redeploy the Render backend.

Temporary testing-only CORS can be:

```text
AIDSSIST_CORS_ORIGINS=*
```

For the final demo, use the exact Vercel URL instead of `*`.
Do not leave wildcard CORS enabled for the hosted demo.

## Verify

Run:

```bash
FRONTEND_URL=https://your-project.vercel.app \
BACKEND_URL=https://aidssist-v3.onrender.com \
./scripts/frontend_live_smoke.sh
```

Then open the Vercel URL in a browser and confirm:

- Page loads.
- API status is online.
- Register/login works.
- CSV upload works.
- Dashboard analysis works.
- Charts render.
- Forecast runs.
- Ask-your-data works.
- Report export/download works.
