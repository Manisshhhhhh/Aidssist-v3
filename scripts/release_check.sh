#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

run() {
  printf "\n==> %s\n" "$*"
  "$@"
}

echo "Aidssist release check"
echo "Root: $ROOT_DIR"

if [[ -n "$(git status --short)" ]]; then
  echo "FAIL: working tree is not clean. Commit, stash, or discard changes before release."
  git status --short
  exit 1
fi
echo "PASS: working tree is clean"

run make test
run make typecheck
run make build

if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  run docker compose config
  run make docker-build
  run make docker-up
  trap 'docker compose down --remove-orphans' EXIT
  run make docker-smoke
else
  echo "SKIP: Docker is not available or the Docker engine is not running."
fi

echo "PASS: release check completed"
