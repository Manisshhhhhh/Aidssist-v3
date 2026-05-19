# Aidssist V3 Release Notes

Date: 2026-05-16
Latest candidate: `3.0.0-rc3`

Aidssist V3 RC1 is the first release-candidate package for local-first autonomous data intelligence workflows. RC3 is the current release-candidate line for Docker-verified CI/CD and release consistency.

## Major Capabilities

- CSV and Excel `.xlsx` upload with validation.
- Dataset metadata, listing, detail, and deletion.
- Deterministic profiling, quality metrics, insights, correlations, and chart recommendations.
- Backend chart-data endpoint and frontend Recharts visualizations.
- Deterministic forecasting with linear regression and moving-average baselines.
- Safe deterministic ask-your-data chat.
- HTML/JSON report export.
- Optional Gemini AI summaries, disabled by default and generated only from deterministic Aidssist outputs.
- User auth, JWT sessions, workspaces, roles, and permissions.
- SQLite metadata persistence with Alembic migrations.
- Database-backed background jobs and worker script.
- Storage abstraction and artifact records.
- Audit logs, request IDs, diagnostics, and structured logging.
- Fail-safe/read-only mode, startup preflight, backups, restore script, and recovery scripts.
- Dockerfiles and Docker Compose packaging.

## Architecture Summary

Backend:

- FastAPI
- Pandas/NumPy/scikit-learn deterministic analytics
- SQLAlchemy + SQLite by default
- Alembic migrations
- local filesystem storage provider
- database-backed jobs

Frontend:

- React + Vite + TypeScript
- Tailwind CSS
- Recharts
- React Three Fiber ambient visual layer
- Material-inspired dark/light UI

## Verification Summary

Completed in the local Codex environment:

- Backend tests: `222 passed`
- Frontend typecheck: passed
- Frontend production build: passed
- Fresh temp Alembic migration to head: passed
- Sync smoke: passed
- Async smoke: passed
- Preflight smoke: passed with documented local artifact warnings
- Backup smoke: passed
- Restore dry-run validation: passed
- Job audit: no queued/running/failed jobs

## Docker Verification Update

- Docker Desktop runtime verification passed on macOS for RC3: Compose build/up, backend health, frontend nginx, sync smoke, async worker smoke, restart persistence, fresh-volume startup, and fresh upload/report smoke.

## RC3 Consistency Update

- RC3 fixes release version consistency after RC2 had already been published against an earlier commit.
- RC3 includes CI/CD hardening, the manual Docker smoke workflow, the local doctor script, the release-check script, and Makefile/documentation improvements.
- GitHub Actions status should be checked in the repository Actions tab after publishing.

## Launch Kit

- [Demo Script](DEMO_SCRIPT.md)
- [Launch Kit Checklist](LAUNCH_KIT.md)
- [Screenshot Guide](SCREENSHOT_GUIDE.md)
- [LinkedIn Post Drafts](LINKEDIN_POST.md)
- [Product One-Pager](PRODUCT_ONE_PAGER.md)

## Known Blockers

- Existing local development DB is not Alembic-stamped and can show existing-table errors; fresh DB migration was verified.
- Local storage audit reports old development artifact drift from earlier runs.
- Gemini runtime smoke is skipped unless a new rotated `GEMINI_API_KEY` is configured.
- Public SaaS deployment needs more hardening: TLS, managed DB/object storage, stronger auth lifecycle, monitoring, backups, file scanning, and operational controls.

## Upgrade Notes

- Run `alembic upgrade head` on a fresh or properly stamped database.
- Use `scripts/sync_filesystem_to_db.py` for older filesystem-only artifacts.
- Keep LLM disabled unless privacy/cost/security review is complete.
- Use `make preflight` after changes.

## Rollback Notes

- Create a backup before upgrading: `make backup`.
- Restore is CLI-only: `backend/scripts/restore_backup.py <backup.zip> --yes`.
- Enable `AIDSSIST_READ_ONLY_MODE=true` during incident triage.
- Use `docker compose down --volumes --remove-orphans` only when intentionally deleting Docker demo data.
