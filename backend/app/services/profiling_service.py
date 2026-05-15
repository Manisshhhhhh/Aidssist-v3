from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

import numpy as np
import pandas as pd

from app.models.analysis_models import (
    AnalysisResult,
    ColumnProfile,
    CorrelationResult,
    DataQuality,
)


DATETIME_PARSE_THRESHOLD = 0.8
BOOLEAN_VALUES = {
    "true",
    "false",
    "yes",
    "no",
    "y",
    "n",
    "1",
    "0",
}


def profile_dataset(dataset_id: str, dataframe: pd.DataFrame) -> AnalysisResult:
    columns = [profile_column(dataframe[column], len(dataframe)) for column in dataframe.columns]
    quality = build_quality_profile(dataframe, columns)
    correlations = build_correlations(dataframe)

    return AnalysisResult(
        dataset_id=dataset_id,
        row_count=int(dataframe.shape[0]),
        column_count=int(dataframe.shape[1]),
        columns=columns,
        quality=quality,
        correlations=correlations,
        recommended_charts=[],
        insights=[],
        created_at=datetime.now(timezone.utc),
    )


def profile_column(series: pd.Series, row_count: int) -> ColumnProfile:
    semantic_type = detect_semantic_type(series)
    missing_count = int(series.isna().sum())
    non_null_count = max(row_count - missing_count, 0)
    unique_count = int(series.nunique(dropna=True))
    sample_values = [to_json_safe(value) for value in series.dropna().head(5).tolist()]

    return ColumnProfile(
        name=str(series.name),
        dtype=str(series.dtype),
        semantic_type=semantic_type,
        missing_count=missing_count,
        missing_percent=round_percent(missing_count, row_count),
        unique_count=unique_count,
        unique_percent=round_percent(unique_count, non_null_count),
        sample_values=sample_values,
        stats=build_column_stats(series, semantic_type),
    )


def detect_semantic_type(series: pd.Series) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return "unknown"

    if pd.api.types.is_bool_dtype(series) or is_boolean_like(non_null):
        return "boolean"

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if looks_datetime_like(non_null) and datetime_parse_ratio(non_null) >= DATETIME_PARSE_THRESHOLD:
        return "datetime"

    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series) or pd.api.types.is_categorical_dtype(series):
        unique_count = int(non_null.nunique())
        unique_percent = unique_count / max(len(non_null), 1) * 100
        average_length = non_null.astype(str).str.len().mean()

        if unique_count <= 20 or unique_percent <= 50:
            return "categorical"
        if average_length >= 30 or unique_percent > 50:
            return "text"

    return "unknown"


def is_boolean_like(series: pd.Series) -> bool:
    normalized = {str(value).strip().lower() for value in series.unique()}
    return 0 < len(normalized) <= 2 and normalized.issubset(BOOLEAN_VALUES)


def datetime_parse_ratio(series: pd.Series) -> float:
    parsed = pd.to_datetime(series, errors="coerce")
    return float(parsed.notna().sum() / max(len(series), 1))


def looks_datetime_like(series: pd.Series) -> bool:
    values = series.astype(str).str.strip()
    if values.empty:
        return False

    date_like = values.str.contains(
        r"(?:\d{4}[-/]\d{1,2}[-/]\d{1,2})|(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        regex=True,
    )
    return bool(date_like.mean() >= 0.5)


def build_column_stats(series: pd.Series, semantic_type: str) -> dict[str, Any]:
    if semantic_type == "numeric":
        numeric = pd.to_numeric(series, errors="coerce")
        return {
            "mean": to_json_safe(numeric.mean()),
            "median": to_json_safe(numeric.median()),
            "min": to_json_safe(numeric.min()),
            "max": to_json_safe(numeric.max()),
            "std": to_json_safe(numeric.std()),
            "q1": to_json_safe(numeric.quantile(0.25)),
            "q3": to_json_safe(numeric.quantile(0.75)),
        }

    if semantic_type == "datetime":
        parsed = pd.to_datetime(series, errors="coerce")
        min_date = parsed.min()
        max_date = parsed.max()
        range_days = None
        if pd.notna(min_date) and pd.notna(max_date):
            range_days = int((max_date - min_date).days)
        return {
            "min_date": to_json_safe(min_date),
            "max_date": to_json_safe(max_date),
            "range_days": range_days,
        }

    if semantic_type in {"categorical", "boolean"}:
        return {"top_values": build_top_values(series)}

    if semantic_type == "text":
        lengths = series.dropna().astype(str).str.len()
        return {
            "average_length": to_json_safe(lengths.mean()),
            "min_length": to_json_safe(lengths.min()),
            "max_length": to_json_safe(lengths.max()),
        }

    return {}


def build_top_values(series: pd.Series) -> list[dict[str, Any]]:
    non_null = series.dropna()
    total = len(non_null)
    top_values: list[dict[str, Any]] = []

    for value, count in non_null.value_counts().head(10).items():
        top_values.append(
            {
                "value": to_json_safe(value),
                "count": int(count),
                "percent": round_percent(int(count), total),
            }
        )

    return top_values


def build_quality_profile(dataframe: pd.DataFrame, columns: list[ColumnProfile]) -> DataQuality:
    row_count, column_count = dataframe.shape
    total_cells = row_count * column_count
    missing_cells = int(dataframe.isna().sum().sum())
    duplicate_rows = int(dataframe.duplicated().sum())
    missing_percent = round_percent(missing_cells, total_cells)
    duplicate_percent = round_percent(duplicate_rows, row_count)
    empty_columns = [column.name for column in columns if column.missing_count == row_count]
    constant_columns = [
        column.name
        for column in columns
        if column.unique_count == 1 and column.missing_count < row_count
    ]

    score = 100
    score -= min(30, missing_percent * 0.3)
    score -= min(20, duplicate_percent * 0.2)
    if empty_columns:
        score -= 10
    if constant_columns:
        score -= 10

    return DataQuality(
        missing_cells=missing_cells,
        missing_percent=missing_percent,
        duplicate_rows=duplicate_rows,
        duplicate_percent=duplicate_percent,
        empty_columns=empty_columns,
        constant_columns=constant_columns,
        quality_score=max(0, min(100, int(round(score)))),
    )


def build_correlations(dataframe: pd.DataFrame) -> list[CorrelationResult]:
    numeric_frame = dataframe.select_dtypes(include=["number"])
    if numeric_frame.shape[1] < 2:
        return []

    correlation_matrix = numeric_frame.corr()
    results: list[CorrelationResult] = []
    columns = list(correlation_matrix.columns)

    for index, column_a in enumerate(columns):
        for column_b in columns[index + 1 :]:
            correlation = correlation_matrix.loc[column_a, column_b]
            safe_correlation = to_json_safe(correlation)
            if safe_correlation is None:
                continue
            if abs(safe_correlation) >= 0.5:
                results.append(
                    CorrelationResult(
                        column_a=str(column_a),
                        column_b=str(column_b),
                        correlation=round(float(safe_correlation), 4),
                    )
                )

    return sorted(results, key=lambda item: abs(item.correlation), reverse=True)[:20]


def round_percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def to_json_safe(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.isoformat()

    if isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, 6)

    if isinstance(value, (datetime,)):
        return value.isoformat()

    if pd.isna(value):
        return None

    return value
