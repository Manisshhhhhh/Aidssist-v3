#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-${AIDSSIST_SMOKE_BASE_URL:-}}"

if [[ -z "$BACKEND_URL" ]]; then
  echo "FAIL: set BACKEND_URL, for example:"
  echo "  BACKEND_URL=https://your-backend-url ./scripts/live_smoke.sh"
  exit 1
fi

BACKEND_URL="${BACKEND_URL%/}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Aidssist live smoke"
echo "Backend: $BACKEND_URL"

if command -v curl >/dev/null 2>&1; then
  curl -fsS "$BACKEND_URL/health" >/dev/null
  echo "PASS: health"
else
  echo "WARN: curl not found; skipping direct health check"
fi

PYTHON_BIN="python3"
if [[ -x "$ROOT_DIR/backend/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/backend/.venv/bin/python"
fi

AIDSSIST_SMOKE_BASE_URL="$BACKEND_URL" "$PYTHON_BIN" "$ROOT_DIR/backend/scripts/smoke_test.py" --base-url "$BACKEND_URL"
