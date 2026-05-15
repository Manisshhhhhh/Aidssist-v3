from __future__ import annotations

from datetime import datetime, timezone
from difflib import get_close_matches
import math
import re
from typing import Any, Optional
from uuid import uuid4

import numpy as np
import pandas as pd
from pandas.errors import ParserError

from app.models.analysis_models import AnalysisResult, ColumnProfile
from app.models.chat_models import ChatRequest, ChatResponse, ChatResult
from app.models.dataset_models import DatasetMetadata
from app.repositories.chat_repository import save_chat_exchange
from app.services import storage_service
from app.services.analysis_service import load_analysis


MAX_RESULT_ROWS = 20


class DatasetQueryNotFoundError(Exception):
    """Raised when a chat request references an unknown dataset."""


class DatasetQueryError(Exception):
    """Raised when chat cannot safely read or answer over a dataset."""


def answer_dataset_question(dataset_id: str, request: ChatRequest) -> ChatResponse:
    metadata = storage_service.load_metadata(dataset_id)
    if metadata is None:
        raise DatasetQueryNotFoundError(f"Dataset '{dataset_id}' was not found.")

    dataframe = _load_dataframe(dataset_id)
    analysis = load_analysis(dataset_id)
    message = request.message.strip()
    conversation_id = request.conversation_id or uuid4().hex

    answer = _dispatch_question(message=message, metadata=metadata, dataframe=dataframe, analysis=analysis)

    response = ChatResponse(
        dataset_id=dataset_id,
        conversation_id=conversation_id,
        message=message,
        answer=answer["answer"],
        intent=answer["intent"],
        confidence=answer["confidence"],
        columns_used=answer["columns_used"],
        result=ChatResult(type=answer["result_type"], data=_json_safe(answer["result_data"])),
        suggested_followups=_suggest_followups(dataframe, analysis, answer["intent"]),
        warnings=answer["warnings"],
        created_at=datetime.now(timezone.utc),
    )
    save_chat_exchange(response)
    return response


def _load_dataframe(dataset_id: str) -> pd.DataFrame:
    original_path = storage_service.get_original_file_path(dataset_id)
    if not original_path.is_file():
        raise DatasetQueryError("Original CSV file is missing.")

    try:
        return pd.read_csv(original_path)
    except (ParserError, UnicodeDecodeError, ValueError) as exc:
        raise DatasetQueryError("Stored CSV file could not be read.") from exc


def _dispatch_question(
    message: str,
    metadata: DatasetMetadata,
    dataframe: pd.DataFrame,
    analysis: Optional[AnalysisResult],
) -> dict[str, Any]:
    normalized = _normalize_text(message)
    lower = message.lower()

    if _looks_like_code_request(lower):
        return _unsupported(
            warning="Code-like requests are not executed. Ask a bounded dataset question instead."
        )

    ambiguity = _detect_ambiguous_column(message, dataframe.columns)
    if ambiguity:
        choices = ", ".join(ambiguity["matches"])
        return {
            "answer": f"I found more than one possible column for '{ambiguity['term']}': {choices}. Please ask again with the exact column name.",
            "intent": "clarification",
            "confidence": 0.55,
            "columns_used": [],
            "result_type": "list",
            "result_data": ambiguity["matches"],
            "warnings": ["Column name was ambiguous."],
        }

    if _matches_any(normalized, ["chart", "visualization", "visualisation", "graph"]):
        return _chart_help(analysis)

    if _matches_any(normalized, ["forecast", "predict", "prediction", "future"]):
        return _forecast_help(dataframe, analysis)

    if _matches_any(normalized, ["missing", "null", "blank", "emptyvalues", "missingdata"]):
        return _missing_values(dataframe, analysis)

    if _matches_any(normalized, ["duplicate", "duplicates", "duplicaterows"]):
        return _duplicates(dataframe, analysis)

    if _matches_any(normalized, ["correlate", "correlation", "correlates"]):
        return _correlation_lookup(message, dataframe, analysis)

    if _matches_any(normalized, ["columns", "columnlist", "showcolumns", "availablecolumns"]):
        return _column_list(dataframe, analysis)

    if _matches_any(normalized, ["summarize", "summary", "whatisin", "rowsandcolumns", "howmanyrows", "howmanycolumns", "dataset"]):
        return _dataset_summary(metadata, dataframe, analysis)

    if _matches_any(normalized, ["topvalues", "mostcommon", "frequent", "frequency"]):
        return _top_values(message, dataframe)

    aggregate = _extract_aggregate(normalized)
    if aggregate and " by " in lower:
        return _groupby_aggregate(message, dataframe, aggregate)

    if _matches_any(normalized, ["top", "bottom", "highest", "lowest"]):
        return _top_bottom_records(message, dataframe)

    if aggregate:
        return _numeric_summary(message, dataframe, aggregate)

    if _matches_any(normalized, ["about", "typeof", "type", "profile", "tellmeabout"]):
        return _column_profile(message, dataframe, analysis)

    return _unsupported()


def _dataset_summary(
    metadata: DatasetMetadata,
    dataframe: pd.DataFrame,
    analysis: Optional[AnalysisResult],
) -> dict[str, Any]:
    row_count = metadata.row_count if metadata.row_count is not None else len(dataframe)
    column_count = metadata.column_count if metadata.column_count is not None else len(dataframe.columns)
    quality = f" Quality score is {analysis.quality.quality_score}/100." if analysis else ""
    answer = (
        f"This dataset has {row_count:,} rows and {column_count:,} columns. "
        f"Columns include: {', '.join(map(str, dataframe.columns[:8]))}."
        f"{quality}"
    )
    return _response("dataset_summary", answer, 0.9, [], "metric", {
        "label": "Dataset size",
        "value": {"rows": row_count, "columns": column_count},
    })


def _column_list(dataframe: pd.DataFrame, analysis: Optional[AnalysisResult]) -> dict[str, Any]:
    if analysis:
        columns = [f"{column.name} ({column.semantic_type})" for column in analysis.columns]
        answer = "Available columns are: " + ", ".join(columns) + "."
        data: list[Any] = [{"name": column.name, "semantic_type": column.semantic_type} for column in analysis.columns]
    else:
        columns = [str(column) for column in dataframe.columns]
        answer = "Available columns are: " + ", ".join(columns) + ". Run analysis for detected semantic types."
        data = columns
    return _response("column_list", answer, 0.9, [], "list", data)


def _column_profile(
    message: str,
    dataframe: pd.DataFrame,
    analysis: Optional[AnalysisResult],
) -> dict[str, Any]:
    column = _find_column(message, dataframe.columns)
    if column is None:
        return _unsupported("I could not identify which column you want profiled.")

    if analysis:
        profile = next((item for item in analysis.columns if item.name == column), None)
        if profile:
            answer = (
                f"{column} is detected as {profile.semantic_type} with dtype {profile.dtype}. "
                f"It has {profile.missing_count} missing values and {profile.unique_count} unique values."
            )
            return _response("column_profile", answer, 0.86, [column], "table", [profile.model_dump()])

    series = dataframe[column]
    answer = f"{column} has dtype {series.dtype}, {int(series.isna().sum())} missing values, and {int(series.nunique(dropna=True))} unique values."
    return _response("column_profile", answer, 0.76, [column], "metric", {
        "label": f"{column} profile",
        "value": {"dtype": str(series.dtype), "missing": int(series.isna().sum()), "unique": int(series.nunique(dropna=True))},
    })


def _missing_values(dataframe: pd.DataFrame, analysis: Optional[AnalysisResult]) -> dict[str, Any]:
    if analysis:
        rows = [
            {
                "column": column.name,
                "missing_count": column.missing_count,
                "missing_percent": column.missing_percent,
            }
            for column in analysis.columns
            if column.missing_count > 0
        ]
        total = analysis.quality.missing_cells
    else:
        rows = [
            {"column": str(column), "missing_count": int(dataframe[column].isna().sum())}
            for column in dataframe.columns
            if dataframe[column].isna().sum() > 0
        ]
        total = sum(row["missing_count"] for row in rows)

    if not rows:
        return _response("missing_values", "No missing values were detected.", 0.86, [], "table", [])

    answer = f"I found {total:,} missing cells across {len(rows)} column(s)."
    return _response("missing_values", answer, 0.9, [row["column"] for row in rows], "table", rows[:MAX_RESULT_ROWS])


def _duplicates(dataframe: pd.DataFrame, analysis: Optional[AnalysisResult]) -> dict[str, Any]:
    duplicate_rows = analysis.quality.duplicate_rows if analysis else int(dataframe.duplicated().sum())
    percent = analysis.quality.duplicate_percent if analysis else round((duplicate_rows / max(len(dataframe), 1)) * 100, 2)
    answer = f"The dataset has {duplicate_rows:,} duplicate row(s), which is {percent}% of rows."
    return _response("duplicates", answer, 0.88, [], "metric", {
        "label": "Duplicate rows",
        "value": duplicate_rows,
    })


def _top_values(message: str, dataframe: pd.DataFrame) -> dict[str, Any]:
    column = _find_column(message, dataframe.columns)
    if column is None:
        return _unsupported("I could not identify the column for top values.")

    counts = dataframe[column].dropna().astype(str).value_counts().head(MAX_RESULT_ROWS)
    rows = [{"value": index, "count": int(value)} for index, value in counts.items()]
    answer = f"The most common values in {column} are: " + ", ".join(
        f"{row['value']} ({row['count']})" for row in rows[:5]
    ) + "."
    return _response("top_values", answer, 0.86, [column], "table", rows)


def _numeric_summary(message: str, dataframe: pd.DataFrame, aggregate: str) -> dict[str, Any]:
    numeric_columns = _numeric_columns(dataframe)
    column = _find_column(message, numeric_columns)
    if column is None:
        return _unsupported("I could not identify a numeric column for that calculation.")

    series = pd.to_numeric(dataframe[column], errors="coerce").dropna()
    if series.empty:
        return _unsupported(f"{column} does not contain numeric values I can summarize.")

    value = _aggregate_series(series, aggregate)
    label = f"{aggregate} {column}"
    answer = f"The {aggregate} of {column} is {_format_value(value)}."
    return _response("numeric_summary", answer, 0.9, [column], "metric", {"label": label, "value": value})


def _groupby_aggregate(message: str, dataframe: pd.DataFrame, aggregate: str) -> dict[str, Any]:
    numeric_columns = _numeric_columns(dataframe)
    target_column = _find_column(message, numeric_columns)
    group_candidates = [column for column in dataframe.columns if column != target_column]
    group_column = _find_column(message.split(" by ", 1)[1], group_candidates) if " by " in message.lower() else None

    if target_column is None or group_column is None:
        return _unsupported("I could not identify both a numeric target and a group column.")

    working = dataframe[[group_column, target_column]].copy()
    working[target_column] = pd.to_numeric(working[target_column], errors="coerce")
    working = working.dropna(subset=[group_column, target_column])
    if working.empty:
        return _unsupported("No valid rows were available for that grouped calculation.")

    grouped = getattr(working.groupby(group_column)[target_column], aggregate if aggregate != "count" else "count")()
    grouped = grouped.sort_values(ascending=False).head(MAX_RESULT_ROWS)
    result_column = f"{target_column}_{aggregate}"
    rows = [{str(group_column): index, result_column: value} for index, value in grouped.items()]
    answer = f"The {aggregate} {target_column} by {group_column} is shown for the top {len(rows)} group(s)."
    return _response("groupby_aggregate", answer, 0.88, [target_column, str(group_column)], "table", rows)


def _top_bottom_records(message: str, dataframe: pd.DataFrame) -> dict[str, Any]:
    numeric_columns = _numeric_columns(dataframe)
    column = _find_column(message, numeric_columns)
    if column is None:
        return _unsupported("I could not identify a numeric column for top or bottom rows.")

    limit_match = re.search(r"\b(top|bottom|highest|lowest)\s+(\d+)", message.lower())
    requested_limit = int(limit_match.group(2)) if limit_match else 5
    limit = min(max(requested_limit, 1), MAX_RESULT_ROWS)
    ascending = any(word in message.lower() for word in ["bottom", "lowest"])
    working = dataframe.copy()
    working[column] = pd.to_numeric(working[column], errors="coerce")
    rows = working.dropna(subset=[column]).sort_values(column, ascending=ascending).head(limit)
    answer = f"Here are the {'bottom' if ascending else 'top'} {len(rows)} row(s) by {column}."
    return _response("top_bottom_records", answer, 0.84, [column], "table", rows.to_dict(orient="records"))


def _correlation_lookup(
    message: str,
    dataframe: pd.DataFrame,
    analysis: Optional[AnalysisResult],
) -> dict[str, Any]:
    if not analysis:
        return _unsupported("Run analysis first to answer correlation questions.")

    mentioned = [column for column in dataframe.columns if _normalized_column(column) in _normalize_text(message)]
    if len(mentioned) >= 2:
        rows = [
            item.model_dump()
            for item in analysis.correlations
            if {item.column_a, item.column_b} == {mentioned[0], mentioned[1]}
        ]
    elif len(mentioned) == 1:
        rows = [
            item.model_dump()
            for item in analysis.correlations
            if mentioned[0] in {item.column_a, item.column_b}
        ]
    else:
        rows = [item.model_dump() for item in analysis.correlations[:MAX_RESULT_ROWS]]

    if not rows:
        return _response("correlation_lookup", "No matching correlations above the threshold were found.", 0.78, mentioned, "table", [])

    answer = f"I found {len(rows)} correlation result(s) from the analysis."
    return _response("correlation_lookup", answer, 0.88, list({col for row in rows for col in [row["column_a"], row["column_b"]]}), "table", rows[:MAX_RESULT_ROWS])


def _chart_help(analysis: Optional[AnalysisResult]) -> dict[str, Any]:
    if not analysis:
        return _unsupported("Run analysis first so I can recommend charts from the dataset profile.")

    rows = [
        {
            "title": chart.title,
            "chart_type": chart.chart_type,
            "x": chart.x,
            "y": chart.y,
            "priority": chart.priority,
            "reason": chart.reason,
        }
        for chart in analysis.recommended_charts[:MAX_RESULT_ROWS]
    ]
    answer = f"The analysis recommends {len(analysis.recommended_charts)} chart(s). The highest priority options are shown."
    return _response("chart_help", answer, 0.9, [], "table", rows)


def _forecast_help(dataframe: pd.DataFrame, analysis: Optional[AnalysisResult]) -> dict[str, Any]:
    if analysis:
        date_columns = [column.name for column in analysis.columns if column.semantic_type == "datetime"]
        numeric = [column.name for column in analysis.columns if column.semantic_type == "numeric"]
    else:
        date_columns = []
        numeric = _numeric_columns(dataframe)

    if not date_columns or not numeric:
        return _response(
            "forecast_help",
            "Forecasting requires at least one datetime column and one numeric column.",
            0.82,
            date_columns + numeric,
            "list",
            [],
        )

    pairs = [f"{target} by {date_columns[0]}" for target in numeric[:5]]
    answer = "Forecast-ready pairs include: " + ", ".join(pairs) + ". Use the forecast panel to run the model."
    return _response("forecast_help", answer, 0.88, date_columns + numeric[:5], "list", pairs)


def _unsupported(answer: Optional[str] = None, warning: Optional[str] = None) -> dict[str, Any]:
    return _response(
        "unsupported",
        answer
        or "I can answer dataset summary, column, missing-value, aggregation, grouping, correlation, chart, and forecast-readiness questions right now.",
        0.35,
        [],
        "text",
        None,
        [warning] if warning else [],
    )


def _response(
    intent: str,
    answer: str,
    confidence: float,
    columns_used: list[str],
    result_type: str,
    result_data: Any,
    warnings: Optional[list[str]] = None,
) -> dict[str, Any]:
    return {
        "answer": answer,
        "intent": intent,
        "confidence": confidence,
        "columns_used": columns_used,
        "result_type": result_type,
        "result_data": result_data,
        "warnings": warnings or [],
    }


def _extract_aggregate(normalized_message: str) -> Optional[str]:
    aliases = {
        "average": "mean",
        "avg": "mean",
        "mean": "mean",
        "total": "sum",
        "sum": "sum",
        "median": "median",
        "minimum": "min",
        "min": "min",
        "maximum": "max",
        "max": "max",
        "standarddeviation": "std",
        "std": "std",
        "count": "count",
    }
    for alias, aggregate in aliases.items():
        if alias in normalized_message:
            return aggregate
    return None


def _aggregate_series(series: pd.Series, aggregate: str) -> float:
    if aggregate == "count":
        return float(series.count())
    if aggregate == "sum":
        return float(series.sum())
    if aggregate == "mean":
        return float(series.mean())
    if aggregate == "median":
        return float(series.median())
    if aggregate == "min":
        return float(series.min())
    if aggregate == "max":
        return float(series.max())
    if aggregate == "std":
        return float(series.std())
    return float(series.mean())


def _numeric_columns(dataframe: pd.DataFrame) -> list[str]:
    numeric: list[str] = []
    for column in dataframe.columns:
        converted = pd.to_numeric(dataframe[column], errors="coerce")
        if converted.notna().any():
            numeric.append(str(column))
    return numeric


def _find_column(message: str, columns: Any) -> Optional[str]:
    column_names = [str(column) for column in columns]
    normalized_message = _normalize_text(message)

    for column in column_names:
        if _normalized_column(column) in normalized_message:
            return column

    tokens = re.findall(r"[A-Za-z0-9]+", message.lower())
    normalized_columns = {_normalized_column(column): column for column in column_names}
    for token in tokens:
        token_norm = _normalize_text(token)
        if token_norm in normalized_columns:
            return normalized_columns[token_norm]
        matches = get_close_matches(token_norm, list(normalized_columns.keys()), n=1, cutoff=0.88)
        if matches:
            return normalized_columns[matches[0]]
    return None


def _detect_ambiguous_column(message: str, columns: Any) -> Optional[dict[str, Any]]:
    column_names = [str(column) for column in columns]
    normalized_columns = {_normalized_column(column): column for column in column_names}
    tokens = [token for token in re.findall(r"[A-Za-z0-9]+", message.lower()) if len(token.strip()) >= 3]

    for token in tokens:
        token_norm = _normalize_text(token)
        if token_norm in normalized_columns:
            continue
        matches = get_close_matches(token_norm, list(normalized_columns.keys()), n=4, cutoff=0.65)
        if len(matches) > 1:
            return {"term": token.strip(), "matches": [normalized_columns[match] for match in matches]}
    return None


def _normalized_column(column: Any) -> str:
    return _normalize_text(str(column))


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _matches_any(normalized_message: str, needles: list[str]) -> bool:
    return any(needle in normalized_message for needle in needles)


def _looks_like_code_request(message: str) -> bool:
    code_patterns = [
        r"\b(run|execute|eval|exec)\b",
        r"\bpython\b",
        r"\bshell\b",
        r"\bterminal\b",
        r"\bsubprocess\b",
        r"\bimport\s+os\b",
        r"\bprint\s*\(",
        r"\brm\s+-rf\b",
        r"\bselect\b.+\bfrom\b",
    ]
    return any(re.search(pattern, message) for pattern in code_patterns)


def _suggest_followups(dataframe: pd.DataFrame, analysis: Optional[AnalysisResult], intent: str) -> list[str]:
    suggestions = ["Summarize this dataset", "Show missing values", "What charts should I use?"]
    numeric = _numeric_columns(dataframe)
    categorical = _categorical_columns(dataframe, analysis)
    datetime_columns = [column.name for column in analysis.columns if column.semantic_type == "datetime"] if analysis else []

    if numeric and categorical:
        suggestions.append(f"Average {numeric[0]} by {categorical[0]}")
    if numeric and datetime_columns:
        suggestions.append(f"Can I forecast {numeric[0]}?")

    return [suggestion for suggestion in suggestions if _normalize_text(suggestion) != _normalize_text(intent)][:4]


def _categorical_columns(dataframe: pd.DataFrame, analysis: Optional[AnalysisResult]) -> list[str]:
    if analysis:
        return [
            column.name
            for column in analysis.columns
            if column.semantic_type in {"categorical", "boolean", "text"}
        ]
    return [
        str(column)
        for column in dataframe.columns
        if str(dataframe[column].dtype) == "object" and dataframe[column].nunique(dropna=True) <= 30
    ]


def _format_value(value: float) -> str:
    return f"{value:,.2f}" if not float(value).is_integer() else f"{value:,.0f}"


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value
