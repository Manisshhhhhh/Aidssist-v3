from __future__ import annotations

from typing import Iterable

import pandas as pd

from app.models.analysis_models import ColumnProfile, CorrelationResult, DataQuality, Insight
from app.services.profiling_service import to_json_safe


SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2, "info": 3}


def generate_insights(
    dataframe: pd.DataFrame,
    columns: list[ColumnProfile],
    quality: DataQuality,
    correlations: list[CorrelationResult],
) -> list[Insight]:
    insights: list[Insight] = []
    insights.extend(missing_value_insights(columns))
    insights.extend(dataset_shape_insights(dataframe, quality))
    insights.extend(column_quality_insights(quality))
    insights.extend(cardinality_insights(columns))
    insights.extend(correlation_insights(correlations))
    insights.extend(numeric_distribution_insights(dataframe, columns))
    insights.extend(datetime_insights(columns))

    return sort_dedupe_and_limit(insights)


def missing_value_insights(columns: list[ColumnProfile]) -> list[Insight]:
    insights: list[Insight] = []
    for column in columns:
        if column.missing_count > 0:
            insights.append(
                Insight(
                    type="missing_values",
                    severity="medium" if column.missing_percent < 20 else "high",
                    title="Missing values detected",
                    message=f"Column {column.name} has {column.missing_count} missing values.",
                    columns=[column.name],
                )
            )
    return insights


def dataset_shape_insights(dataframe: pd.DataFrame, quality: DataQuality) -> list[Insight]:
    row_count, column_count = dataframe.shape
    insights: list[Insight] = []

    if quality.quality_score >= 90:
        insights.append(
            Insight(
                type="data_quality",
                severity="info",
                title="High data quality score",
                message=f"Dataset quality score is {quality.quality_score}/100.",
                columns=[],
            )
        )
    elif quality.quality_score >= 70:
        insights.append(
            Insight(
                type="data_quality",
                severity="medium",
                title="Medium data quality score",
                message=f"Dataset quality score is {quality.quality_score}/100.",
                columns=[],
            )
        )
    else:
        insights.append(
            Insight(
                type="data_quality",
                severity="high",
                title="Low data quality score",
                message=f"Dataset quality score is {quality.quality_score}/100.",
                columns=[],
            )
        )

    if row_count < 30:
        insights.append(
            Insight(
                type="dataset_size",
                severity="low",
                title="Small dataset warning",
                message=f"The dataset has {row_count} rows, which may limit statistical confidence.",
                columns=[],
            )
        )

    if column_count > 50:
        insights.append(
            Insight(
                type="dataset_shape",
                severity="medium",
                title="Wide dataset warning",
                message=f"The dataset has {column_count} columns, which may require focused analysis.",
                columns=[],
            )
        )

    return insights


def column_quality_insights(quality: DataQuality) -> list[Insight]:
    insights: list[Insight] = []

    if quality.duplicate_rows > 0:
        insights.append(
            Insight(
                type="duplicates",
                severity="medium",
                title="Duplicate rows detected",
                message=f"The dataset contains {quality.duplicate_rows} duplicate rows.",
                columns=[],
            )
        )

    if quality.empty_columns:
        insights.append(
            Insight(
                type="empty_columns",
                severity="high",
                title="Empty columns detected",
                message=f"Empty columns found: {', '.join(quality.empty_columns)}.",
                columns=quality.empty_columns,
            )
        )

    if quality.constant_columns:
        insights.append(
            Insight(
                type="constant_columns",
                severity="low",
                title="Constant columns detected",
                message=f"Constant columns found: {', '.join(quality.constant_columns)}.",
                columns=quality.constant_columns,
            )
        )

    return insights


def cardinality_insights(columns: list[ColumnProfile]) -> list[Insight]:
    insights: list[Insight] = []
    for column in columns:
        if column.semantic_type in {"categorical", "text"} and column.unique_percent >= 80 and column.unique_count > 20:
            insights.append(
                Insight(
                    type="high_cardinality",
                    severity="low",
                    title="High-cardinality column detected",
                    message=f"Column {column.name} has {column.unique_count} unique values.",
                    columns=[column.name],
                )
            )
    return insights


def correlation_insights(correlations: list[CorrelationResult]) -> list[Insight]:
    insights: list[Insight] = []
    for correlation in correlations:
        if correlation.correlation >= 0.7:
            insights.append(
                Insight(
                    type="correlation",
                    severity="high",
                    title="Strong positive relationship detected",
                    message=(
                        f"{correlation.column_a} and {correlation.column_b} have a strong "
                        f"positive correlation of {correlation.correlation}."
                    ),
                    columns=[correlation.column_a, correlation.column_b],
                )
            )
        elif correlation.correlation <= -0.7:
            insights.append(
                Insight(
                    type="correlation",
                    severity="high",
                    title="Strong negative relationship detected",
                    message=(
                        f"{correlation.column_a} and {correlation.column_b} have a strong "
                        f"negative correlation of {correlation.correlation}."
                    ),
                    columns=[correlation.column_a, correlation.column_b],
                )
            )
    return insights


def numeric_distribution_insights(
    dataframe: pd.DataFrame,
    columns: list[ColumnProfile],
) -> list[Insight]:
    insights: list[Insight] = []
    for column in columns:
        if column.semantic_type != "numeric":
            continue

        numeric = pd.to_numeric(dataframe[column.name], errors="coerce").dropna()
        skew = to_json_safe(numeric.skew())
        if skew is not None and abs(skew) > 1:
            insights.append(
                Insight(
                    type="skew",
                    severity="low",
                    title="Skewed numeric distribution detected",
                    message=f"Column {column.name} has skew of {round(float(skew), 3)}.",
                    columns=[column.name],
                )
            )

        outlier_count = count_iqr_outliers(numeric)
        if outlier_count > 0:
            insights.append(
                Insight(
                    type="outliers",
                    severity="medium",
                    title="Potential outliers detected",
                    message=f"Column {column.name} has {outlier_count} potential outliers using the IQR rule.",
                    columns=[column.name],
                )
            )

    return insights


def datetime_insights(columns: list[ColumnProfile]) -> list[Insight]:
    insights: list[Insight] = []
    for column in columns:
        if column.semantic_type == "datetime":
            min_date = column.stats.get("min_date")
            max_date = column.stats.get("max_date")
            range_days = column.stats.get("range_days")
            if min_date and max_date:
                insights.append(
                    Insight(
                        type="datetime_range",
                        severity="info",
                        title="Date range detected",
                        message=(
                            f"Column {column.name} spans from {min_date} to {max_date}"
                            f" across {range_days} days."
                        ),
                        columns=[column.name],
                    )
                )
    return insights


def count_iqr_outliers(series: pd.Series) -> int:
    if series.empty:
        return 0
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    if iqr <= 0:
        return 0
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return int(((series < lower_bound) | (series > upper_bound)).sum())


def sort_dedupe_and_limit(insights: Iterable[Insight]) -> list[Insight]:
    deduped: dict[tuple[str, str, tuple[str, ...]], Insight] = {}
    for insight in insights:
        key = (insight.type, insight.title, tuple(insight.columns))
        existing = deduped.get(key)
        if existing is None or SEVERITY_RANK[insight.severity] < SEVERITY_RANK[existing.severity]:
            deduped[key] = insight

    return sorted(
        deduped.values(),
        key=lambda insight: (
            SEVERITY_RANK.get(insight.severity, 99),
            insight.type,
            insight.title,
            ",".join(insight.columns),
        ),
    )[:30]
