# Aidssist V3 Product One-Pager

## Product Name

Aidssist v3

## One-Line Pitch

Aidssist v3 turns uploaded CSV and Excel datasets into deterministic analysis, charts, forecasts, grounded Q&A, and exportable reports from one local-first workspace.

## Problem

Business users often have useful data trapped in spreadsheets, but getting from a raw file to trustworthy insights usually requires manual profiling, chart setup, statistical interpretation, repeated questions, and report formatting.

Many AI-first tools also blur the line between grounded analysis and generated explanation, which can create risk when the underlying data has quality issues or ambiguous columns.

## Solution

Aidssist v3 provides a deterministic-first data intelligence workflow. It validates and profiles datasets, surfaces quality issues, recommends and renders charts, forecasts time-series data with assumptions and warnings, answers supported dataset questions safely, and exports professional reports.

Optional Gemini summaries can explain deterministic Aidssist outputs, but they do not replace the source-of-truth analysis.

## Core Workflow

1. Upload CSV or Excel data.
2. Review dataset registry and metadata.
3. Open the analysis dashboard.
4. Inspect quality, columns, insights, correlations, and charts.
5. Generate forecasts when datetime and numeric columns exist.
6. Ask grounded dataset questions.
7. Export HTML or JSON reports.

## Key Features

- CSV and Excel `.xlsx` upload.
- Dataset registry and detail views.
- Data quality scoring.
- Column profiling and semantic type detection.
- Deterministic insights.
- Correlation analysis.
- Backend chart-data endpoint and frontend visualizations.
- Time-series forecasting with assumptions and warnings.
- Safe deterministic ask-your-data chat.
- Optional Gemini AI summary from deterministic outputs.
- HTML/JSON report export.
- Background jobs for heavier operations.
- User auth, workspaces, roles, and permissions.
- Audit logs, diagnostics, backups, and fail-safe mode.

## Technical Architecture

- Backend: FastAPI, Pandas, NumPy, scikit-learn, SQLAlchemy, Alembic.
- Frontend: React, Vite, TypeScript, Tailwind CSS, Recharts.
- Storage: local provider abstraction with artifact records.
- Persistence: SQLite by default, PostgreSQL-compatible model direction.
- Jobs: database-backed background job records and worker script.
- Packaging: Dockerfiles, Docker Compose, Makefile, GitHub Actions.

## Security And Governance

- Optional API key protection for internal demos.
- User authentication with JWT access tokens.
- Workspace roles: owner, admin, editor, viewer.
- Request IDs and structured logs.
- Audit events for important actions.
- Rate limiting and upload size limits.
- Read-only and safe mode controls.
- Backup, restore, artifact repair, and job recovery scripts.

## Current Status

Aidssist v3 is a release-candidate local product build suitable for demos and controlled internal evaluation.

## Limitations

- Not ready for open public internet deployment.
- No managed production database or object storage configured by default.
- No full SaaS tenant isolation review.
- No email verification, password reset, MFA, or OAuth.
- No malware scanning for uploaded files.
- Optional Gemini AI summary requires a rotated server-side API key and privacy review.

## Next Roadmap

- Production deployment hardening.
- Managed PostgreSQL and object storage.
- Stronger auth lifecycle and tenant isolation.
- Observability integration with external monitoring.
- PDF export.
- More connector integrations.
- Reviewed LLM explanation workflows for sensitive data.
