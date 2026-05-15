from __future__ import annotations

import json
import re
from typing import Any, Optional

from app.core.config import get_settings
from app.models.analysis_models import AnalysisResult
from app.models.dataset_models import DatasetMetadata
from app.models.llm_models import AiSummaryRequest
from app.services.report_service import load_latest_forecast


SYSTEM_INSTRUCTION = """You are Aidssist V3's optional explanation layer.
Use only the deterministic analysis facts provided by Aidssist.
Do not invent metrics, rows, causes, predictions, or recommendations.
State limitations and uncertainty clearly.
Do not claim certainty about forecasts.
Do not mention local file paths, internal implementation details, secrets, or API keys."""


def build_ai_summary_prompt(
    metadata: DatasetMetadata,
    analysis: AnalysisResult,
    request: AiSummaryRequest,
) -> tuple[str, dict[str, bool]]:
    forecast = load_latest_forecast(metadata.dataset_id) if request.include_forecast else None
    facts = {
        "task": {
            "tone": request.tone,
            "format": request.format,
            "instructions": [
                "Summarize the dataset for a business/data audience.",
                "Ground every statement in the supplied deterministic outputs.",
                "Highlight data quality, strongest insights, chart opportunities, and forecast caveats when available.",
                "If using bullets, keep them concise and scannable.",
            ],
        },
        "dataset": {
            "dataset_id": metadata.dataset_id,
            "original_filename": metadata.original_filename,
            "file_size_bytes": metadata.file_size_bytes,
            "row_count": metadata.row_count,
            "column_count": metadata.column_count,
            "columns": (metadata.columns or [])[:100],
        },
        "analysis": {
            "row_count": analysis.row_count,
            "column_count": analysis.column_count,
            "quality": analysis.quality.model_dump(mode="json"),
            "columns": [column_summary(column) for column in analysis.columns[:50]],
            "insights": [insight.model_dump(mode="json") for insight in analysis.insights[:20]],
            "correlations": [corr.model_dump(mode="json") for corr in analysis.correlations[:12]],
            "recommended_charts": (
                [chart.model_dump(mode="json") for chart in analysis.recommended_charts[:12]]
                if request.include_charts
                else []
            ),
        },
        "forecast": forecast,
        "privacy_constraints": {
            "raw_csv_rows_sent": False,
            "full_dataset_sent": False,
            "sample_values_limited": True,
        },
    }
    prompt = truncate_prompt(redact_sensitive(json.dumps(facts, ensure_ascii=False, indent=2)))
    return prompt, {
        "used_analysis": True,
        "used_forecast": forecast is not None,
        "used_charts": request.include_charts and bool(analysis.recommended_charts),
    }


def column_summary(column) -> dict[str, Any]:  # noqa: ANN001
    stats = dict(column.stats)
    if "top_values" in stats and isinstance(stats["top_values"], list):
        stats["top_values"] = stats["top_values"][:5]
    return {
        "name": column.name,
        "semantic_type": column.semantic_type,
        "missing_percent": column.missing_percent,
        "unique_count": column.unique_count,
        "sample_values": [redact_sensitive(str(value))[:80] for value in column.sample_values[:3]],
        "stats": stats,
    }


def truncate_prompt(prompt: str) -> str:
    limit = max(1000, get_settings().llm_max_input_chars)
    if len(prompt) <= limit:
        return prompt
    suffix = "\n\n[Input truncated to Aidssist configured safety limit.]"
    return prompt[: max(0, limit - len(suffix))] + suffix


def redact_sensitive(value: str) -> str:
    patterns = [
        r"AIza[0-9A-Za-z_-]{20,}",
        r"sk-[0-9A-Za-z_-]{20,}",
        r"Bearer\s+[0-9A-Za-z._-]+",
        r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*['\"]?[^,'\"\s}]+",
    ]
    redacted = value
    for pattern in patterns:
        redacted = re.sub(pattern, "[redacted]", redacted)
    return redacted
