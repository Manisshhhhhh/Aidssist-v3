from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Optional

import numpy as np
import pandas as pd
from pandas.errors import ParserError

from app.models.analysis_models import AnalysisResult, ChartSpec
from app.models.chart_models import ChartDataResponse
from app.services import storage_service
from app.services.analysis_service import load_analysis


class DatasetNotFoundError(Exception):
    """Raised when a requested dataset cannot be found."""


class AnalysisRequiredError(Exception):
    """Raised when chart data is requested before analysis has been run."""


class ChartNotFoundError(Exception):
    """Raised when a requested chart id is not part of the analysis output."""


class ChartDataError(Exception):
    """Raised when chart data cannot be generated from the stored CSV."""


SUPPORTED_TIME_RANGES = {
    "1d": pd.DateOffset(days=1),
    "1w": pd.DateOffset(weeks=1),
    "1m": pd.DateOffset(months=1),
    "1q": pd.DateOffset(months=3),
    "1y": pd.DateOffset(years=1),
    "3y": pd.DateOffset(years=3),
    "5y": pd.DateOffset(years=5),
}


def get_chart_data(dataset_id: str, chart_id: str, time_range: Optional[str] = None) -> ChartDataResponse:
    if storage_service.load_metadata(dataset_id) is None:
        raise DatasetNotFoundError(f"Dataset '{dataset_id}' was not found.")

    analysis = load_analysis(dataset_id)
    if analysis is None:
        raise AnalysisRequiredError("Run analysis before requesting chart data.")

    chart = find_chart(analysis, chart_id)
    if chart is None:
        raise ChartNotFoundError(f"Chart '{chart_id}' was not found.")

    dataframe = load_dataset_frame(dataset_id)
    normalized_time_range = normalize_time_range(time_range)
    data, metadata = build_chart_payload(dataframe, chart, normalized_time_range)

    return ChartDataResponse(
        dataset_id=dataset_id,
        chart_id=chart.chart_id,
        title=chart.title,
        description=chart.description,
        chart_type=chart.chart_type,
        x=chart.x,
        y=chart.y,
        series=chart.series,
        data=data,
        metadata=metadata,
        created_at=datetime.now(timezone.utc),
    )


def find_chart(analysis: AnalysisResult, chart_id: str) -> Optional[ChartSpec]:
    for chart in analysis.recommended_charts:
        if chart.chart_id == chart_id:
            return chart
    return None


def load_dataset_frame(dataset_id: str) -> pd.DataFrame:
    original_path = storage_service.get_original_file_path(dataset_id)
    if not original_path.is_file():
        raise ChartDataError("Original CSV file is missing.")

    try:
        return pd.read_csv(original_path)
    except (ParserError, UnicodeDecodeError, ValueError) as exc:
        raise ChartDataError("Stored CSV file could not be read.") from exc


def build_chart_payload(
    dataframe: pd.DataFrame,
    chart: ChartSpec,
    time_range: Optional[str] = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    chart_type = chart.chart_type
    if chart_type in {"line", "area"}:
        return build_time_series_data(dataframe, chart, time_range)
    if chart_type == "bar":
        return build_bar_data(dataframe, chart)
    if chart_type == "pie":
        return build_pie_data(dataframe, chart)
    if chart_type == "histogram":
        return build_histogram_data(dataframe, chart)
    if chart_type == "scatter":
        return build_scatter_data(dataframe, chart)
    if chart_type == "heatmap":
        return build_heatmap_data(dataframe, chart)
    if chart_type == "box":
        return build_box_data(dataframe, chart)

    raise ChartDataError(f"Unsupported chart type '{chart_type}'.")


def build_time_series_data(
    dataframe: pd.DataFrame,
    chart: ChartSpec,
    time_range: Optional[str] = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require_columns(dataframe, [chart.x, chart.y])
    aggregation = get_aggregation(chart, default="sum")

    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(dataframe[chart.x], errors="coerce"),
            "value": pd.to_numeric(dataframe[chart.y], errors="coerce"),
        }
    ).dropna()
    grouped = aggregate_frame(frame, "date", "value", aggregation)
    grouped = grouped.sort_values("date")
    grouped = apply_time_range(grouped, time_range)
    grouped = grouped.head(500)

    data = [
        {
            "x": row.date.isoformat(),
            "y": safe_value(row.value),
            "label": row.date.isoformat(),
        }
        for row in grouped.itertuples(index=False)
    ]
    chart_metadata = metadata(chart, aggregation, len(data))
    chart_metadata["time_range"] = time_range or "all"
    return data, chart_metadata


def build_bar_data(
    dataframe: pd.DataFrame,
    chart: ChartSpec,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require_columns(dataframe, [chart.x])
    limit = int(chart.config.get("limit", 10))

    if chart.y is not None:
        require_columns(dataframe, [chart.y])
        aggregation = get_aggregation(chart, default="mean")
        frame = pd.DataFrame(
            {
                "category": dataframe[chart.x].astype(str),
                "value": pd.to_numeric(dataframe[chart.y], errors="coerce"),
            }
        ).dropna()
        grouped = aggregate_frame(frame, "category", "value", aggregation)
    else:
        aggregation = "count"
        grouped = (
            dataframe[chart.x]
            .dropna()
            .astype(str)
            .value_counts()
            .rename_axis("category")
            .reset_index(name="value")
        )

    grouped = grouped.sort_values("value", ascending=False).head(limit)
    data = [
        {"x": safe_value(row.category), "y": safe_value(row.value), "label": safe_value(row.category)}
        for row in grouped.itertuples(index=False)
    ]
    return data, metadata(chart, aggregation, len(data))


def build_pie_data(
    dataframe: pd.DataFrame,
    chart: ChartSpec,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require_columns(dataframe, [chart.x])
    limit = int(chart.config.get("limit", 6))
    counts = dataframe[chart.x].dropna().astype(str).value_counts()
    top_counts = counts.head(limit)
    data = [
        {"x": safe_value(label), "y": safe_value(count), "label": safe_value(label)}
        for label, count in top_counts.items()
    ]

    if len(counts) > limit:
        other_count = int(counts.iloc[limit:].sum())
        if other_count > 0:
            data.append({"x": "Other", "y": other_count, "label": "Other"})

    return data, metadata(chart, "count", len(data))


def build_histogram_data(
    dataframe: pd.DataFrame,
    chart: ChartSpec,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    numeric_column = chart.x if chart.x in dataframe.columns else chart.y
    if numeric_column is None:
        raise ChartDataError("Histogram requires a numeric column.")
    require_columns(dataframe, [numeric_column])

    values = pd.to_numeric(dataframe[numeric_column], errors="coerce").dropna().to_numpy(dtype=float)
    if len(values) == 0:
        raise ChartDataError("Histogram column does not contain numeric values.")

    bin_count = int(min(20, max(5, math.sqrt(len(values)))))
    counts, bin_edges = np.histogram(values, bins=bin_count)
    data: list[dict[str, Any]] = []

    for index, count in enumerate(counts):
        start = float(bin_edges[index])
        end = float(bin_edges[index + 1])
        label = f"{format_bin(start)} - {format_bin(end)}"
        data.append(
            {
                "x": label,
                "y": int(count),
                "bin_start": safe_value(start),
                "bin_end": safe_value(end),
                "label": label,
            }
        )

    return data, metadata(chart, "count", len(data))


def build_scatter_data(
    dataframe: pd.DataFrame,
    chart: ChartSpec,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    require_columns(dataframe, [chart.x, chart.y])
    frame = pd.DataFrame(
        {
            "x": pd.to_numeric(dataframe[chart.x], errors="coerce"),
            "y": pd.to_numeric(dataframe[chart.y], errors="coerce"),
        }
    ).dropna()
    frame = frame.head(1000)

    data = [
        {
            "x": safe_value(row.x),
            "y": safe_value(row.y),
            "label": f"row {index + 1}",
        }
        for index, row in enumerate(frame.itertuples(index=False))
    ]
    return data, metadata(chart, None, len(data))


def build_heatmap_data(
    dataframe: pd.DataFrame,
    chart: ChartSpec,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    numeric_frame = dataframe.select_dtypes(include=["number"])
    if numeric_frame.shape[1] < 3:
        raise ChartDataError("Heatmap requires at least 3 numeric columns.")

    matrix = numeric_frame.corr()
    data: list[dict[str, Any]] = []
    for column_a in matrix.columns:
        for column_b in matrix.columns:
            value = safe_value(matrix.loc[column_a, column_b])
            if value is None:
                continue
            data.append(
                {
                    "x": str(column_a),
                    "y": str(column_b),
                    "value": value,
                    "label": f"{column_a}/{column_b}",
                }
            )

    return data, metadata(chart, "pearson", len(data))


def build_box_data(
    dataframe: pd.DataFrame,
    chart: ChartSpec,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    numeric_column = chart.x if chart.x in dataframe.columns else chart.y
    if numeric_column is None:
        raise ChartDataError("Box chart requires a numeric column.")
    require_columns(dataframe, [numeric_column])

    series = pd.to_numeric(dataframe[numeric_column], errors="coerce").dropna()
    if series.empty:
        raise ChartDataError("Box chart column does not contain numeric values.")

    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    outlier_count = 0
    if iqr > 0:
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_count = int(((series < lower) | (series > upper)).sum())

    data = [
        {
            "x": numeric_column,
            "min": safe_value(series.min()),
            "q1": safe_value(q1),
            "median": safe_value(series.median()),
            "q3": safe_value(q3),
            "max": safe_value(series.max()),
            "mean": safe_value(series.mean()),
            "outlier_count": outlier_count,
            "label": numeric_column,
        }
    ]
    return data, metadata(chart, None, len(data))


def require_columns(dataframe: pd.DataFrame, columns: list[Any]) -> None:
    missing_columns = [column for column in columns if column is not None and column not in dataframe.columns]
    if missing_columns:
        raise ChartDataError(f"Missing required chart columns: {', '.join(map(str, missing_columns))}.")


def aggregate_frame(frame: pd.DataFrame, group_column: str, value_column: str, aggregation: str) -> pd.DataFrame:
    if aggregation == "sum":
        return frame.groupby(group_column, as_index=False)[value_column].sum()
    if aggregation == "mean":
        return frame.groupby(group_column, as_index=False)[value_column].mean()
    if aggregation == "count":
        return frame.groupby(group_column, as_index=False)[value_column].count()
    raise ChartDataError(f"Unsupported aggregation '{aggregation}'.")


def get_aggregation(chart: ChartSpec, default: str) -> str:
    aggregation = chart.config.get("aggregation", default)
    return str(aggregation)


def metadata(chart: ChartSpec, aggregation: Optional[str], row_count: int) -> dict[str, Any]:
    return {
        "x_label": chart.x,
        "y_label": chart.y,
        "aggregation": aggregation,
        "row_count": row_count,
    }


def normalize_time_range(time_range: Optional[str]) -> Optional[str]:
    if time_range in {None, "", "all"}:
        return None
    if time_range not in SUPPORTED_TIME_RANGES:
        raise ChartDataError("Unsupported time range. Use all, 1d, 1w, 1m, 1q, 1y, 3y, or 5y.")
    return time_range


def apply_time_range(frame: pd.DataFrame, time_range: Optional[str]) -> pd.DataFrame:
    if time_range is None or frame.empty:
        return frame

    latest_date = frame["date"].max()
    start_date = latest_date - SUPPORTED_TIME_RANGES[time_range]
    filtered = frame[frame["date"] >= start_date]
    return filtered if not filtered.empty else frame


def safe_value(value: Any) -> Any:
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
    if pd.isna(value):
        return None
    return value


def format_bin(value: float) -> str:
    safe = safe_value(value)
    if isinstance(safe, float):
        return f"{safe:.2f}".rstrip("0").rstrip(".")
    return str(safe)
