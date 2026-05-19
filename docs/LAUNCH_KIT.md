# Aidssist V3 Launch Kit

Use this checklist before sharing Aidssist v3 publicly or in a controlled demo.

## Repository

- [ ] GitHub repo verified: <https://github.com/Manisshhhhhh/Aidssist-v3>
- [ ] Latest `main` branch pushed.
- [ ] Release status in `VERSION` and README is correct.
- [ ] Existing release tags are preserved.
- [ ] README polished and readable.
- [ ] Release notes updated.

## Safety

- [ ] No real `.env` files committed.
- [ ] No API keys, Gemini keys, JWT secrets, GitHub tokens, or credentials committed.
- [ ] No SQLite DB files committed.
- [ ] No uploaded datasets, generated reports, backups, `node_modules`, `.venv`, `web/dist`, or zip files committed.
- [ ] Secret scan completed.
- [ ] Known limitations documented.

## Demo Materials

- [ ] Demo script rehearsed.
- [ ] Screenshots captured using `docs/SCREENSHOT_GUIDE.md`.
- [ ] Short demo video recorded.
- [ ] Product one-pager reviewed.
- [ ] LinkedIn post selected and edited for final tone.

## Runtime Verification

- [ ] `make doctor` passes.
- [ ] `make release-check` passes.
- [ ] Docker build verified.
- [ ] Docker smoke verified.
- [ ] Backend health endpoint checked.
- [ ] Frontend nginx endpoint checked.
- [ ] Worker/async smoke checked if using background jobs.
- [ ] Storage audit checked.
- [ ] Job audit checked.

## Product Demo Flow

- [ ] Upload `sample_data/sales_timeseries.csv`.
- [ ] Confirm dataset appears in registry.
- [ ] Open dashboard.
- [ ] Confirm overview, quality, insights, charts, and correlations render.
- [ ] Generate forecast.
- [ ] Ask "summarize this dataset".
- [ ] Ask "average sales by region".
- [ ] Generate HTML report.
- [ ] Download/open report.
- [ ] Confirm optional AI summary behavior is clear if LLM is disabled.

## Publication

- [ ] GitHub Actions checked.
- [ ] Docker Smoke workflow is visible and triggerable.
- [ ] LinkedIn post ready.
- [ ] Screenshots/video attached.
- [ ] Demo limitations stated plainly.

## Final Status

- [ ] Ready for controlled demo.
- [ ] Ready for public GitHub visibility, if intentionally made public.
- [ ] Not positioned as production SaaS without further hardening.
