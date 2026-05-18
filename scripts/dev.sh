#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
WEB_DIR="$ROOT_DIR/web"
BACKEND_URL="${AIDSSIST_DEV_BACKEND_URL:-http://127.0.0.1:8000}"
FRONTEND_URL="${AIDSSIST_DEV_FRONTEND_URL:-http://127.0.0.1:5173}"

BACKEND_PID=""
WEB_PID=""

cleanup() {
  if [[ -n "$BACKEND_PID" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "$WEB_PID" ]]; then
    kill "$WEB_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

wait_for_url() {
  local url="$1"
  local label="$2"
  local attempts="${3:-60}"

  for _ in $(seq 1 "$attempts"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  echo "$label did not become reachable at $url" >&2
  return 1
}

ensure_backend_venv() {
  cd "$BACKEND_DIR"
  if [[ ! -x ".venv/bin/python" ]] || ! .venv/bin/python -c "import sys" >/dev/null 2>&1; then
    rm -rf .venv
    python3 -m venv .venv
  fi

  if ! .venv/bin/python -c "import fastapi, uvicorn, alembic" >/dev/null 2>&1; then
    .venv/bin/python -m pip install -r requirements.txt
  fi
}

ensure_web_deps() {
  cd "$WEB_DIR"
  if [[ ! -d "node_modules" ]]; then
    npm install
  fi
}

start_backend() {
  if curl -fsS "$BACKEND_URL/health" >/dev/null 2>&1; then
    echo "Backend already running: $BACKEND_URL"
    return
  fi

  ensure_backend_venv
  cd "$BACKEND_DIR"
  .venv/bin/python -c "from app.db.init_db import init_db; init_db()"

  local reload_args=(--reload --reload-dir app)
  if [[ "${AIDSSIST_BACKEND_RELOAD:-true}" == "false" ]]; then
    reload_args=()
  fi

  .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 "${reload_args[@]}" &
  BACKEND_PID=$!
  wait_for_url "$BACKEND_URL/health" "Backend"
}

start_frontend() {
  if curl -fsS "$FRONTEND_URL" >/dev/null 2>&1; then
    echo "Frontend already running: $FRONTEND_URL"
    return
  fi

  ensure_web_deps
  cd "$WEB_DIR"
  npm run dev -- --host 127.0.0.1 &
  WEB_PID=$!
  wait_for_url "$FRONTEND_URL" "Frontend"
}

start_backend
start_frontend

if [[ "${AIDSSIST_OPEN_BROWSER:-false}" == "true" ]]; then
  open -a Safari "$FRONTEND_URL/" || open "$FRONTEND_URL/"
fi

echo "Aidssist V3 is running:"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  $BACKEND_URL"
echo "Press Control-C to stop services started by this command."

wait
