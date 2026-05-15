from __future__ import annotations

from datetime import datetime, timezone
import html
import json
import math
from pathlib import Path
import re
from typing import Any, Optional
from uuid import uuid4

from app.models.analysis_models import AnalysisResult
from app.models.dataset_models import DatasetMetadata
from app.models.forecast_models import ForecastResponse
from app.models.llm_models import AiSummaryRequest
from app.models.report_models import ReportRequest, ReportResponse
from app.repositories.chat_repository import latest_chat_exchanges
from app.repositories.artifact_repository import list_dataset_artifacts
from app.repositories.forecast_repository import latest_forecast_record
from app.repositories.report_repository import create_report_record, get_report_record
from app.services.audit_service import record_event
from app.services import artifact_service
from app.services import storage_service
from app.services.analysis_service import load_analysis


class ReportDatasetNotFoundError(Exception):
    """Raised when a dataset does not exist."""


class ReportValidationError(Exception):
    """Raised when a report cannot be generated."""


class ReportNotFoundError(Exception):
    """Raised when a generated report cannot be found."""


def generate_report(dataset_id: str, request: ReportRequest, current_user=None, audit_request=None) -> ReportResponse:
    metadata = storage_service.load_metadata(dataset_id)
    if metadata is None:
        raise ReportDatasetNotFoundError(f"Dataset '{dataset_id}' was not found.")

    analysis = load_analysis(dataset_id)
    if analysis is None:
        raise ReportValidationError("Run analysis before generating a report.")

    created_at = datetime.now(timezone.utc)
    report_id = f"{created_at.strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"
    payload = build_report_payload(metadata, analysis, request, created_at, current_user=current_user, audit_request=audit_request)
    json_key = storage_service.get_report_key(dataset_id, report_id, "report.json")
    html_key = storage_service.get_report_key(dataset_id, report_id, "report.html")
    manifest_key = storage_service.get_report_key(dataset_id, report_id, "manifest.json")
    json_stored = storage_service.get_provider().save_text(
        json_key,
        json.dumps(json_safe(payload), indent=2, ensure_ascii=False),
        "application/json",
    )
    html_stored = storage_service.get_provider().save_text(
        html_key,
        render_html_report(payload),
        "text/html",
    )
    storage_service.get_provider().save_text(
        manifest_key,
        json.dumps({"format": request.format, "created_at": created_at.isoformat()}, indent=2),
        "application/json",
    )
    json_path = storage_service.get_provider().get_local_path(json_stored.key)
    html_path = storage_service.get_provider().get_local_path(html_stored.key)
    if json_path is None or html_path is None:
        raise ReportValidationError("Report storage path is unavailable.")

    filename = f"aidssist_report_{short_id(dataset_id)}.{request.format}"
    response = ReportResponse(
        dataset_id=dataset_id,
        report_id=report_id,
        format=request.format,
        filename=filename,
        download_url=f"/datasets/{dataset_id}/reports/{report_id}/download",
        created_at=created_at,
    )
    create_report_record(response, report_path=html_path, json_path=json_path)
    artifact_service.record_artifact(
        artifact_type="report_html",
        stored=html_stored,
        filename="report.html",
        dataset_id=dataset_id,
        metadata={"report_id": report_id, "format": request.format},
    )
    artifact_service.record_artifact(
        artifact_type="report_json",
        stored=json_stored,
        filename="report.json",
        dataset_id=dataset_id,
        metadata={"report_id": report_id, "format": request.format},
    )
    return response


def get_report_file(dataset_id: str, report_id: str, preferred_format: Optional[str] = None) -> tuple[Path, str, str]:
    metadata = storage_service.load_metadata(dataset_id)
    if metadata is None:
        raise ReportDatasetNotFoundError(f"Dataset '{dataset_id}' was not found.")

    safe_report_id = sanitize_component(report_id)
    artifact_file = get_report_artifact_file(dataset_id, safe_report_id, preferred_format)
    if artifact_file is not None:
        report_file, report_format = artifact_file
        media_type = "text/html" if report_format == "html" else "application/json"
        filename = f"aidssist_report_{short_id(dataset_id)}.{report_format}"
        return report_file, media_type, filename

    record = get_report_record(dataset_id, safe_report_id)
    if record is not None:
        report_format = preferred_format if preferred_format in {"html", "json"} else record.format
        report_file = Path(record.report_path if report_format == "html" else record.json_path)
        dataset_dir = storage_service.get_dataset_dir(dataset_id).resolve()
        if report_file.is_file() and is_relative_to(report_file.resolve(), dataset_dir):
            media_type = "text/html" if report_format == "html" else "application/json"
            filename = f"aidssist_report_{short_id(dataset_id)}.{report_format}"
            return report_file, media_type, filename

    report_dir = get_report_dir(dataset_id, safe_report_id)
    if not report_dir.is_dir():
        raise ReportNotFoundError("Report was not found.")

    report_format = preferred_format if preferred_format in {"html", "json"} else infer_report_format(report_dir)
    report_file = report_dir / f"report.{report_format}"
    if not report_file.is_file():
        raise ReportNotFoundError("Report was not found.")

    media_type = "text/html" if report_format == "html" else "application/json"
    filename = f"aidssist_report_{short_id(dataset_id)}.{report_format}"
    return report_file, media_type, filename


def get_report_artifact_file(dataset_id: str, report_id: str, preferred_format: Optional[str]) -> Optional[tuple[Path, str]]:
    preferred = preferred_format if preferred_format in {"html", "json"} else None
    provider = storage_service.get_provider()
    for artifact in list_dataset_artifacts(dataset_id):
        metadata = {}
        if artifact.metadata_json:
            try:
                metadata = json.loads(artifact.metadata_json)
            except json.JSONDecodeError:
                metadata = {}
        if metadata.get("report_id") != report_id:
            continue
        report_format = preferred or metadata.get("format")
        if report_format not in {"html", "json"}:
            report_format = "html"
        if artifact.artifact_type != f"report_{report_format}":
            continue
        if not provider.exists(artifact.storage_key):
            continue
        local_path = provider.get_local_path(artifact.storage_key)
        if local_path is not None and local_path.is_file():
            return local_path, report_format
    return None


def build_report_payload(
    metadata: DatasetMetadata,
    analysis: AnalysisResult,
    request: ReportRequest,
    created_at: datetime,
    current_user=None,
    audit_request=None,
) -> dict[str, Any]:
    forecast = load_latest_forecast(metadata.dataset_id) if request.include_forecast else None
    if request.include_chat_summary:
        exchanges = latest_chat_exchanges(metadata.dataset_id, limit=5)
        chat_summary = (
            {"available": True, "exchanges": exchanges}
            if exchanges
            else {"available": False, "message": "No persisted chat history is available for this dataset."}
        )
    else:
        chat_summary = None
    ai_summary = build_ai_summary_section(metadata.dataset_id, request, current_user=current_user, audit_request=audit_request)

    return {
        "dataset": {
            "dataset_id": metadata.dataset_id,
            "dataset_id_short": short_id(metadata.dataset_id),
            "original_filename": metadata.original_filename,
            "stored_filename": metadata.stored_filename,
            "file_size_bytes": metadata.file_size_bytes,
            "content_type": metadata.content_type,
            "created_at": metadata.created_at.isoformat(),
            "row_count": metadata.row_count,
            "column_count": metadata.column_count,
            "columns": metadata.columns or [],
        },
        "analysis": {
            "overview": {
                "row_count": analysis.row_count,
                "column_count": analysis.column_count,
                "created_at": analysis.created_at.isoformat(),
            },
            "quality": analysis.quality.model_dump(mode="json"),
            "insights": [insight.model_dump(mode="json") for insight in analysis.insights[:30]],
            "correlations": [correlation.model_dump(mode="json") for correlation in analysis.correlations[:20]],
            "recommended_charts": (
                [chart.model_dump(mode="json") for chart in analysis.recommended_charts[:20]]
                if request.include_charts
                else []
            ),
        },
        "forecast": forecast,
        "chat_summary": chat_summary,
        "ai_summary": ai_summary,
        "created_at": created_at.isoformat(),
        "report_type": "Aidssist V3 dataset intelligence report",
    }


def build_ai_summary_section(dataset_id: str, request: ReportRequest, current_user=None, audit_request=None) -> Optional[dict[str, Any]]:
    if not request.include_ai_summary:
        return None

    from app.services.llm_service import (
        AiSummaryProviderError,
        AiSummaryUnavailableError,
        AiSummaryValidationError,
        create_ai_summary,
        latest_ai_summary,
    )

    summary = latest_ai_summary(dataset_id)
    if summary is not None:
        record_event(
            "report.ai_summary.included",
            "include",
            "success",
            actor_user_id=current_user.id if current_user else None,
            dataset_id=dataset_id,
            metadata={"source": "latest_artifact", "provider": summary.get("provider"), "model": summary.get("model")},
            request=audit_request,
        )
        return {"available": True, "source": "latest_artifact", "summary": summary}

    try:
        generated = create_ai_summary(
            dataset_id,
            AiSummaryRequest(include_forecast=request.include_forecast, include_charts=request.include_charts),
            current_user=current_user,
            request=audit_request,
        )
        record_event(
            "report.ai_summary.included",
            "include",
            "success",
            actor_user_id=current_user.id if current_user else None,
            dataset_id=dataset_id,
            metadata={"source": "generated", "provider": generated.provider, "model": generated.model},
            request=audit_request,
        )
        return {"available": True, "source": "generated", "summary": generated.model_dump(mode="json")}
    except AiSummaryUnavailableError as exc:
        return {"available": False, "message": str(exc)}
    except (AiSummaryValidationError, AiSummaryProviderError) as exc:
        return {"available": False, "message": f"AI summary was requested but could not be generated: {str(exc)}"}


def load_latest_forecast(dataset_id: str) -> Optional[dict[str, Any]]:
    latest_record = latest_forecast_record(dataset_id)
    if latest_record is not None:
        forecast_paths = [Path(latest_record.forecast_path)]
    else:
        dataset_dir = storage_service.get_dataset_dir(dataset_id)
        forecast_paths = sorted(
            dataset_dir.glob("forecast_*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    if not forecast_paths:
        return None

    with forecast_paths[0].open("r", encoding="utf-8") as forecast_file:
        payload = json.load(forecast_file)
    forecast = ForecastResponse.model_validate(payload)
    return {
        "date_column": forecast.date_column,
        "target_column": forecast.target_column,
        "model_used": forecast.model_used,
        "frequency": forecast.frequency,
        "periods": forecast.periods,
        "metrics": forecast.metrics.model_dump(mode="json"),
        "assumptions": forecast.assumptions,
        "warnings": forecast.warnings,
        "forecast_points": [point.model_dump(mode="json") for point in forecast.forecast_points[:8]],
        "created_at": forecast.created_at.isoformat(),
    }


def render_html_report(payload: dict[str, Any]) -> str:
    dataset = payload["dataset"]
    analysis = payload["analysis"]
    quality = analysis["quality"]
    forecast = payload["forecast"]
    chat_summary = payload["chat_summary"]
    ai_summary = payload.get("ai_summary")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Aidssist V3 Report - {e(dataset["original_filename"])}</title>
  <style>
    :root {{ color-scheme: light; --ink: #1f2937; --muted: #5f6673; --line: #d8dee8; --panel: #f7f9fc; --brand: #1565c0; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: #ffffff; line-height: 1.55; }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 42px 28px 60px; }}
    header {{ border-bottom: 2px solid var(--line); padding-bottom: 22px; margin-bottom: 28px; }}
    h1 {{ margin: 0; font-size: 34px; letter-spacing: -0.02em; }}
    h2 {{ margin: 34px 0 14px; font-size: 20px; color: #111827; }}
    h3 {{ margin: 20px 0 8px; font-size: 15px; color: #111827; }}
    p {{ margin: 0 0 10px; }}
    .eyebrow {{ color: var(--brand); font-size: 12px; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; }}
    .muted {{ color: var(--muted); }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid var(--line); border-radius: 14px; background: var(--panel); padding: 14px; }}
    .metric {{ font-size: 24px; font-weight: 750; color: #111827; }}
    table {{ width: 100%; border-collapse: collapse; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; margin-top: 10px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 10px 12px; text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ background: #eef3f9; font-weight: 700; }}
    tr:last-child td {{ border-bottom: 0; }}
    ul {{ margin: 8px 0 0; padding-left: 20px; }}
    .pill {{ display: inline-block; border: 1px solid var(--line); border-radius: 999px; padding: 2px 8px; margin: 2px 4px 2px 0; font-size: 12px; color: var(--muted); }}
    .notice {{ border-left: 4px solid var(--brand); padding: 12px 14px; background: #eef6ff; border-radius: 8px; }}
    @media print {{ main {{ padding: 20px; }} .card, table {{ break-inside: avoid; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <p class="eyebrow">Aidssist V3</p>
    <h1>Dataset Intelligence Report</h1>
    <p class="muted">{e(dataset["original_filename"])} · ID {e(dataset["dataset_id_short"])} · {e(payload["created_at"])}</p>
  </header>

  <section>
    <h2>Dataset Overview</h2>
    <div class="grid">
      {metric_card("Rows", dataset.get("row_count"))}
      {metric_card("Columns", dataset.get("column_count"))}
      {metric_card("File size", format_bytes(dataset.get("file_size_bytes")))}
      {metric_card("Quality", f'{quality.get("quality_score", "n/a")}/100')}
    </div>
    <h3>Columns</h3>
    <p>{''.join(f'<span class="pill">{e(column)}</span>' for column in dataset.get("columns", []))}</p>
  </section>

  <section>
    <h2>Data Quality</h2>
    {key_value_table([
        ("Missing cells", quality.get("missing_cells")),
        ("Missing percent", percent_value(quality.get("missing_percent"))),
        ("Duplicate rows", quality.get("duplicate_rows")),
        ("Duplicate percent", percent_value(quality.get("duplicate_percent"))),
        ("Empty columns", join_values(quality.get("empty_columns"))),
        ("Constant columns", join_values(quality.get("constant_columns"))),
    ])}
  </section>

  <section>
    <h2>Key Insights</h2>
    {insights_table(analysis.get("insights", []))}
  </section>

  <section>
    <h2>Recommended Charts</h2>
    {charts_table(analysis.get("recommended_charts", []))}
  </section>

  <section>
    <h2>Correlations</h2>
    {correlations_table(analysis.get("correlations", []))}
  </section>

  <section>
    <h2>Forecast Summary</h2>
    {forecast_section(forecast)}
  </section>

  <section>
    <h2>AI Summary</h2>
    {ai_summary_section(ai_summary)}
  </section>

  <section>
    <h2>Chat Summary</h2>
    {chat_section(chat_summary)}
  </section>
</main>
</body>
</html>"""


def metric_card(label: str, value: Any) -> str:
    return f'<div class="card"><p class="muted">{e(label)}</p><p class="metric">{e(format_value(value))}</p></div>'


def key_value_table(rows: list[tuple[str, Any]]) -> str:
    body = "".join(f"<tr><th>{e(label)}</th><td>{e(format_value(value))}</td></tr>" for label, value in rows)
    return f"<table><tbody>{body}</tbody></table>"


def insights_table(insights: list[dict[str, Any]]) -> str:
    if not insights:
        return '<p class="notice">No deterministic insights were generated.</p>'
    rows = "".join(
        f"<tr><td>{e(item.get('severity'))}</td><td>{e(item.get('title'))}</td><td>{e(item.get('message'))}</td><td>{e(join_values(item.get('columns')))}</td></tr>"
        for item in insights
    )
    return f"<table><thead><tr><th>Severity</th><th>Title</th><th>Message</th><th>Columns</th></tr></thead><tbody>{rows}</tbody></table>"


def charts_table(charts: list[dict[str, Any]]) -> str:
    if not charts:
        return '<p class="notice">Chart recommendations were not included in this report.</p>'
    rows = "".join(
        f"<tr><td>{e(item.get('title'))}</td><td>{e(item.get('chart_type'))}</td><td>{e(item.get('x'))}</td><td>{e(item.get('y'))}</td><td>{e(item.get('priority'))}</td><td>{e(item.get('reason'))}</td></tr>"
        for item in charts
    )
    return f"<table><thead><tr><th>Title</th><th>Type</th><th>X</th><th>Y</th><th>Priority</th><th>Reason</th></tr></thead><tbody>{rows}</tbody></table>"


def correlations_table(correlations: list[dict[str, Any]]) -> str:
    if not correlations:
        return '<p class="notice">No strong numeric correlations were detected.</p>'
    rows = "".join(
        f"<tr><td>{e(item.get('column_a'))}</td><td>{e(item.get('column_b'))}</td><td>{e(item.get('correlation'))}</td></tr>"
        for item in correlations
    )
    return f"<table><thead><tr><th>Column A</th><th>Column B</th><th>Correlation</th></tr></thead><tbody>{rows}</tbody></table>"


def forecast_section(forecast: Optional[dict[str, Any]]) -> str:
    if not forecast:
        return '<p class="notice">No forecast has been generated for this dataset.</p>'

    metrics = forecast.get("metrics", {})
    summary = key_value_table(
        [
            ("Model", forecast.get("model_used")),
            ("Date column", forecast.get("date_column")),
            ("Target column", forecast.get("target_column")),
            ("Frequency", forecast.get("frequency")),
            ("Periods", forecast.get("periods")),
            ("MAE", metrics.get("mae")),
            ("RMSE", metrics.get("rmse")),
            ("MAPE", metrics.get("mape")),
        ]
    )
    points = "".join(
        f"<tr><td>{e(point.get('date'))}</td><td>{e(point.get('predicted_value'))}</td><td>{e(point.get('lower_bound'))}</td><td>{e(point.get('upper_bound'))}</td></tr>"
        for point in forecast.get("forecast_points", [])
    )
    assumptions = "".join(f"<li>{e(item)}</li>" for item in forecast.get("assumptions", []))
    warnings = "".join(f"<li>{e(item)}</li>" for item in forecast.get("warnings", []))
    return (
        summary
        + "<h3>Forecast Points</h3>"
        + f"<table><thead><tr><th>Date</th><th>Predicted</th><th>Lower</th><th>Upper</th></tr></thead><tbody>{points}</tbody></table>"
        + f"<h3>Assumptions</h3><ul>{assumptions}</ul>"
        + f"<h3>Warnings</h3><ul>{warnings}</ul>"
    )


def chat_section(chat_summary: Optional[dict[str, Any]]) -> str:
    if not chat_summary:
        return '<p class="notice">Chat summary was not requested for this report.</p>'
    if chat_summary.get("exchanges"):
        rows = "".join(
            f"<tr><td>{e(item.get('question'))}</td><td>{e(item.get('answer'))}</td><td>{e(item.get('intent'))}</td></tr>"
            for item in chat_summary["exchanges"]
        )
        return f"<table><thead><tr><th>Question</th><th>Answer</th><th>Intent</th></tr></thead><tbody>{rows}</tbody></table>"
    return f'<p class="notice">{e(chat_summary.get("message"))}</p>'


def ai_summary_section(ai_summary: Optional[dict[str, Any]]) -> str:
    if not ai_summary:
        return '<p class="notice">AI summary was not requested for this report.</p>'
    if not ai_summary.get("available"):
        return f'<p class="notice">{e(ai_summary.get("message") or "AI summary is unavailable.")}</p>'
    summary = ai_summary.get("summary") or {}
    text = summary.get("summary") if isinstance(summary, dict) else None
    warnings = summary.get("warnings", []) if isinstance(summary, dict) else []
    warning_list = "".join(f"<li>{e(item)}</li>" for item in warnings)
    return (
        '<p class="notice">Generated from Aidssist deterministic analysis outputs.</p>'
        + f"<p>{e(text or 'No AI summary text was available.')}</p>"
        + (f"<h3>Warnings</h3><ul>{warning_list}</ul>" if warning_list else "")
    )


def get_report_dir(dataset_id: str, report_id: str) -> Path:
    return storage_service.get_dataset_dir(dataset_id) / "reports" / sanitize_component(report_id)


def infer_report_format(report_dir: Path) -> str:
    manifest_path = report_dir / "manifest.json"
    if manifest_path.is_file():
        with manifest_path.open("r", encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)
        if manifest.get("format") in {"html", "json"}:
            return manifest["format"]
    if (report_dir / "report.html").is_file():
        return "html"
    return "json"


def sanitize_component(value: str) -> str:
    safe_value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return safe_value or "report"


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def short_id(dataset_id: str) -> str:
    return sanitize_component(dataset_id)[:12]


def e(value: Any) -> str:
    return html.escape(format_value(value), quote=True)


def format_value(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return "n/a"
        return f"{value:.4g}"
    if isinstance(value, list):
        return join_values(value)
    return str(value)


def join_values(values: Any) -> str:
    if not values:
        return "None"
    if isinstance(values, list):
        return ", ".join(format_value(value) for value in values)
    return format_value(values)


def percent_value(value: Any) -> str:
    return "n/a" if value is None else f"{format_value(value)}%"


def format_bytes(value: Any) -> str:
    if not isinstance(value, int):
        return "n/a"
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(nested_value) for key, nested_value in value.items()}
    if isinstance(value, list):
        return [json_safe(nested_value) for nested_value in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    return value
