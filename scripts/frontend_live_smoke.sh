#!/usr/bin/env bash
set -euo pipefail

FRONTEND_URL="${FRONTEND_URL:-}"
BACKEND_URL="${BACKEND_URL:-https://aidssist-v3.onrender.com}"

if [[ -z "$FRONTEND_URL" ]]; then
  echo "FAIL: set FRONTEND_URL, for example:"
  echo "  FRONTEND_URL=https://your-project.vercel.app BACKEND_URL=https://aidssist-v3.onrender.com ./scripts/frontend_live_smoke.sh"
  exit 1
fi

FRONTEND_URL="${FRONTEND_URL%/}"
BACKEND_URL="${BACKEND_URL%/}"

status_code() {
  curl -L -sS -o /dev/null -w "%{http_code}" "$1"
}

backend_status="$(status_code "$BACKEND_URL/health")"
frontend_status="$(status_code "$FRONTEND_URL")"

echo "Backend health:  $BACKEND_URL/health -> $backend_status"
echo "Frontend root:   $FRONTEND_URL -> $frontend_status"

if [[ "$backend_status" != "200" ]]; then
  echo "FAIL: backend /health must return HTTP 200"
  exit 1
fi

if [[ "$frontend_status" != "200" && "$frontend_status" != "304" ]]; then
  echo "FAIL: frontend root must return HTTP 200 or 304"
  exit 1
fi

cat <<EOF
PASS: live frontend/backend endpoints are reachable.

Next manual browser checks:
1. Open $FRONTEND_URL
2. Confirm API status is online.
3. Register or log in.
4. Upload sample_data/sales_timeseries.csv.
5. Open dashboard, confirm charts, forecast, chat, and report export.
EOF
