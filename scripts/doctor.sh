#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATUS=0

pass() {
  printf "PASS: %s\n" "$1"
}

fail() {
  printf "FAIL: %s\n" "$1"
  STATUS=1
}

warn() {
  printf "WARN: %s\n" "$1"
}

check_command() {
  local name="$1"
  local required="${2:-true}"
  if command -v "$name" >/dev/null 2>&1; then
    pass "$name found: $(command -v "$name")"
  elif [[ "$required" == "true" ]]; then
    fail "$name is required but was not found"
  else
    warn "$name not found"
  fi
}

check_port() {
  local port="$1"
  local label="$2"
  if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    warn "port $port is already in use ($label); dev scripts may reuse or conflict with it"
  else
    pass "port $port is available for $label"
  fi
}

cd "$ROOT_DIR"

echo "Aidssist doctor"
echo "Root: $ROOT_DIR"

check_command git true
check_command python3 true
check_command node true
check_command npm true
check_command docker false

if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    pass "docker compose available: $(docker compose version)"
  else
    fail "docker compose is required for Docker verification but is not available"
  fi

  if docker info >/dev/null 2>&1; then
    pass "Docker engine is running"
  else
    warn "Docker CLI exists, but the Docker engine is not running"
  fi
fi

[[ -f ".env.example" ]] && pass ".env.example exists" || fail ".env.example missing"
[[ -f ".env.docker.example" ]] && pass ".env.docker.example exists" || fail ".env.docker.example missing"
[[ -f "backend/requirements.txt" ]] && pass "backend/requirements.txt exists" || fail "backend/requirements.txt missing"
[[ -f "web/package-lock.json" ]] && pass "web/package-lock.json exists" || fail "web/package-lock.json missing"

if [[ -f ".env" ]]; then
  warn ".env exists locally; confirm it contains no real secrets before sharing logs"
else
  pass ".env is absent; using defaults/placeholders"
fi

check_port 8000 "backend"
check_port 5173 "Vite dev frontend"
check_port 8080 "Docker nginx frontend"

if git status --short | grep -q .; then
  warn "working tree has local changes"
else
  pass "working tree is clean"
fi

exit "$STATUS"
