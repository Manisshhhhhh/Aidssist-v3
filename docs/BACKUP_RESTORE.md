# Backup And Restore

Aidssist backups are local zip archives. Restore is intentionally CLI-only because it can overwrite the SQLite database and local storage.

## Create A Backup

API:

```bash
curl -X POST http://127.0.0.1:8000/backups \
  -H "Content-Type: application/json" \
  -d '{"include_storage":true,"include_reports":true}'
```

CLI:

```bash
cd backend
.venv/bin/python scripts/create_backup.py
```

Makefile:

```bash
make backup
```

Backups are written to `AIDSSIST_BACKUP_DIR`, defaulting to `./backups`.

## List And Download Backups

```bash
curl http://127.0.0.1:8000/backups
curl -OJ http://127.0.0.1:8000/backups/{backup_id}/download
```

When user auth is enabled, backup APIs are admin-only.

## Included Content

- SQLite database file when using SQLite
- dataset storage root
- report storage root
- `manifest.json` with app version, database type, storage backend, and record counts

Backups exclude `.env` files, previous backup zips, virtualenvs, `node_modules`, `dist`, Python caches, and build/runtime junk.

## Restore

Stop the backend first.

Dry validation:

```bash
cd backend
.venv/bin/python scripts/restore_backup.py ../backups/aidssist_backup_YYYYMMDD_HHMMSS_xxxxxxxx.zip
```

Restore:

```bash
cd backend
.venv/bin/python scripts/restore_backup.py ../backups/aidssist_backup_YYYYMMDD_HHMMSS_xxxxxxxx.zip --yes
```

The restore script:

- verifies `manifest.json`
- rejects zip path traversal
- refuses to run if the backend appears active on `127.0.0.1:8000`, unless `--force` is passed
- creates a pre-restore backup before overwriting files

## Verify A Restore

```bash
make preflight
cd backend && .venv/bin/python scripts/smoke_test.py
cd backend && .venv/bin/python scripts/storage_audit.py
cd backend && .venv/bin/python scripts/job_audit.py
```

## Limitations

- Restore is not transactional across DB and files.
- PostgreSQL backups are not implemented; use database-native backups for PostgreSQL.
- Object storage restore is not implemented.
- Backups are not encrypted by Aidssist; protect the backup directory.
