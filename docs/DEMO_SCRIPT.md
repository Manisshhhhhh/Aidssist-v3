# Aidssist V3 Demo Script

Target length: 2-3 minutes.

## 1. Opening

"Aidssist v3 is an AI-powered data intelligence platform built for turning raw business datasets into usable analysis, charts, forecasts, answers, and exportable reports from one local workspace.

The important design choice is that Aidssist is deterministic first. Uploads, profiling, insights, forecasts, charts, chat answers, reports, permissions, jobs, audit logs, and backups all work without relying on an LLM to invent answers."

## 2. Upload

"I’ll start by uploading a CSV or Excel file. The upload area accepts local files, validates the dataset, stores it safely, and registers it in the dataset registry.

On the right, the registry shows recent datasets so I can return to prior work without re-uploading."

## 3. Analysis

"Once I open a dataset, Aidssist runs an analysis profile. The dashboard summarizes row and column counts, data quality, missing values, duplicates, column types, statistical profiles, correlations, deterministic insights, and recommended charts.

This gives me the shape of the dataset before I make decisions from it."

## 4. Forecast

"For time-series data, I can choose a date column and a numeric target, select the forecast horizon, and generate a forecast.

Aidssist shows historical values, forecast values, metrics where available, assumptions, and warnings. It does not make certainty claims; it presents the model output with its limits."

## 5. Ask Data

"The ask-your-data panel is a safe deterministic Q&A layer. I can ask questions like 'summarize this dataset' or 'average sales by region.'

The system answers from the uploaded dataset and analysis outputs. It does not execute user code, SQL, shell commands, or arbitrary formulas."

## 6. AI Summary

"Aidssist also has an optional Gemini-backed AI summary layer. It is off by default and only generates explanations from Aidssist's deterministic outputs, such as quality metrics, insights, chart recommendations, correlations, and forecasts.

The deterministic analysis remains the source of truth. The AI layer is for narrative explanation, not raw-data authority."

## 7. Reports

"When the analysis is ready, I can export a professional HTML or JSON report. Reports include dataset overview, data quality, insights, chart recommendations, correlations, forecast summaries if available, and optional AI summary notes.

Report generation can run synchronously or through background jobs for heavier workflows."

## 8. Engineering Foundation

"Under the hood, Aidssist v3 includes user accounts, workspaces, roles and permissions, database-backed metadata, local storage artifacts, background jobs, audit logs, request IDs, diagnostics, backups, fail-safe mode, Docker packaging, and CI/CD checks.

That means it is not only a demo screen. It has the foundation of a real internal data product."

## 9. Closing

"Aidssist v3 is now a release-candidate product: local-first, Docker verified, documented, and ready for controlled demos. The next steps are production hardening, managed infrastructure, and a reviewed deployment model before public internet use."
