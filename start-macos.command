#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
WEB_DIR="$ROOT_DIR/web"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${WEB_PID:-}" ]]; then
    kill "$WEB_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

cd "$BACKEND_DIR"
if [[ ! -x ".venv/bin/python" ]] || ! .venv/bin/python -c "import sys" >/dev/null 2>&1; then
  rm -rf .venv
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app &
BACKEND_PID=$!

cd "$WEB_DIR"
if [[ ! -d "node_modules" ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm was not found. Install Node.js from https://nodejs.org/ or Homebrew, then run this again."
    exit 1
  fi
  npm install
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm was not found. Install Node.js from https://nodejs.org/ or Homebrew, then run this again."
  exit 1
fi

npm run dev -- --host 127.0.0.1 &
WEB_PID=$!

sleep 2
open -a Safari "http://127.0.0.1:5173/" || open "http://127.0.0.1:5173/"

echo "Aidssist V3 is running:"
echo "  Frontend: http://127.0.0.1:5173/"
echo "  Backend:  http://127.0.0.1:8000/"
echo "  Safari:   opens automatically when available"
echo "Press Control-C to stop both servers."

wait
