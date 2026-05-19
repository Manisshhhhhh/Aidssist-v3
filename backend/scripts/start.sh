#!/usr/bin/env sh
set -eu

if [ "${AIDSSIST_RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Running Alembic migrations..."
  alembic upgrade head
fi

mkdir -p \
  "${AIDSSIST_STORAGE_LOCAL_ROOT:-/data/datasets}" \
  "${AIDSSIST_REPORTS_LOCAL_ROOT:-/data/reports}" \
  "${AIDSSIST_BACKUP_DIR:-/data/backups}"

exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
