# Frontend Smoke Test

## Start Services

Backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
```

Frontend:

```bash
cd web
npm run dev
```

Open <http://127.0.0.1:5173/>.

## Manual Flow

1. Upload `sample_data/sales_timeseries.csv`.
2. Confirm dashboard opens and analysis sections render.
3. Confirm chart panel renders real charts.
4. In Forecasting, select `date` and `sales`; generate a forecast.
5. Confirm forecast chart, metrics, assumptions, and warnings render.
6. In Ask your data, ask:
   - `summarize this dataset`
   - `average sales by region`
   - `what charts should I use?`
7. Generate an HTML report and open it.
8. Generate a JSON report and open it.
9. Toggle light/dark theme and confirm readability.
10. Upload `sample_data/data_quality_issues.csv`.
11. Confirm missing values, duplicates, and quality insights appear.
12. Upload `sample_data/no_forecast_dataset.csv`.
13. Confirm charts and chat work.
14. Confirm forecast empty state appears.
15. Resize to mobile width and repeat a quick upload/dashboard scan.
16. Enable reduced motion in browser/system settings and confirm the 3D visual layer falls back quietly.
17. Stop backend and confirm API offline/error states are clear.
