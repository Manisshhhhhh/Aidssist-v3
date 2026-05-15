from __future__ import annotations

import re
from typing import Optional

from app.models.analysis_models import AnalysisResult, ChartSpec, ColumnProfile, CorrelationResult


MAX_RECOMMENDED_CHARTS = 20
MAX_CATEGORY_NUMERIC_CHARTS = 10
TREND_NAME_HINTS = ("sales", "revenue", "profit", "amount", "total", "count", "value", "price")


def recommend_charts(analysis: AnalysisResult) -> list[ChartSpec]:
    columns = analysis.columns
    numeric_columns = [column for column in columns if column.semantic_type == "numeric"]
    categorical_columns = [
        column
        for column in columns
        if column.semantic_type in {"categorical", "boolean"} and is_low_to_moderate_cardinality(column)
    ]
    datetime_columns = [column for column in columns if column.semantic_type == "datetime"]

    charts: list[ChartSpec] = []
    charts.extend(recommend_time_charts(datetime_columns, numeric_columns))
    charts.extend(recommend_correlation_charts(analysis.correlations))
    charts.extend(recommend_categorical_numeric_charts(categorical_columns, numeric_columns))
    charts.extend(recommend_numeric_distribution_charts(numeric_columns))
    charts.extend(recommend_categorical_frequency_charts(categorical_columns))
    charts.extend(recommend_heatmap(numeric_columns))

    return sort_and_limit_charts(charts)


def recommend_time_charts(
    datetime_columns: list[ColumnProfile],
    numeric_columns: list[ColumnProfile],
) -> list[ChartSpec]:
    charts: list[ChartSpec] = []
    for date_column in datetime_columns[:2]:
        for numeric_column in numeric_columns[:5]:
            charts.append(
                make_chart(
                    chart_type="line",
                    x=date_column.name,
                    y=numeric_column.name,
                    title=f"{title_case(numeric_column.name)} over {title_case(date_column.name)}",
                    description=f"Shows how {numeric_column.name} changes over time.",
                    priority=95,
                    reason="A datetime column and numeric column were detected.",
                    config={"aggregation": "sum", "limit": 50},
                )
            )
            if is_trend_metric(numeric_column.name):
                charts.append(
                    make_chart(
                        chart_type="area",
                        x=date_column.name,
                        y=numeric_column.name,
                        title=f"{title_case(numeric_column.name)} trend area",
                        description=f"Highlights the trend shape for {numeric_column.name} over time.",
                        priority=90,
                        reason=f"{numeric_column.name} appears to be a trend-style numeric metric.",
                        config={"aggregation": "sum", "limit": 50},
                    )
                )
    return charts


def recommend_correlation_charts(correlations: list[CorrelationResult]) -> list[ChartSpec]:
    charts: list[ChartSpec] = []
    for correlation in correlations:
        priority = min(94, 70 + int(abs(correlation.correlation) * 24))
        charts.append(
            make_chart(
                chart_type="scatter",
                x=correlation.column_a,
                y=correlation.column_b,
                title=f"{title_case(correlation.column_a)} vs {title_case(correlation.column_b)}",
                description=(
                    f"Shows the relationship between {correlation.column_a} and "
                    f"{correlation.column_b}."
                ),
                priority=priority,
                reason=f"The columns have correlation {correlation.correlation}.",
                config={"trendline": True, "limit": 500},
            )
        )
    return charts


def recommend_categorical_numeric_charts(
    categorical_columns: list[ColumnProfile],
    numeric_columns: list[ColumnProfile],
) -> list[ChartSpec]:
    charts: list[ChartSpec] = []
    for category_column in categorical_columns:
        for numeric_column in numeric_columns:
            aggregation = "sum" if is_additive_metric(numeric_column.name) else "mean"
            charts.append(
                make_chart(
                    chart_type="bar",
                    x=category_column.name,
                    y=numeric_column.name,
                    title=f"{title_case(numeric_column.name)} by {title_case(category_column.name)}",
                    description=f"Compares {aggregation} {numeric_column.name} across {category_column.name}.",
                    priority=88,
                    reason=f"{category_column.name} is categorical and {numeric_column.name} is numeric.",
                    config={"aggregation": aggregation, "limit": 10},
                )
            )
            if len(charts) >= MAX_CATEGORY_NUMERIC_CHARTS:
                return charts
    return charts


def recommend_numeric_distribution_charts(numeric_columns: list[ColumnProfile]) -> list[ChartSpec]:
    charts: list[ChartSpec] = []
    for numeric_column in numeric_columns:
        if numeric_column.name in {"index", "id"}:
            continue
        charts.append(
            make_chart(
                chart_type="histogram",
                x=numeric_column.name,
                y=None,
                title=f"{title_case(numeric_column.name)} distribution",
                description=f"Shows the distribution of {numeric_column.name}.",
                priority=65,
                reason=f"{numeric_column.name} is numeric.",
                config={"bins": 30, "limit": 1000},
            )
        )
        if has_outliers(numeric_column) or appears_skewed(numeric_column):
            charts.append(
                make_chart(
                    chart_type="box",
                    x=numeric_column.name,
                    y=None,
                    title=f"{title_case(numeric_column.name)} spread",
                    description=f"Shows spread, quartiles, and potential outliers for {numeric_column.name}.",
                    priority=72,
                    reason=f"{numeric_column.name} appears skewed or has potential outliers.",
                    config={"show_outliers": True},
                )
            )
    return charts


def recommend_categorical_frequency_charts(categorical_columns: list[ColumnProfile]) -> list[ChartSpec]:
    charts: list[ChartSpec] = []
    for category_column in categorical_columns:
        charts.append(
            make_chart(
                chart_type="bar",
                x=category_column.name,
                y=None,
                title=f"{title_case(category_column.name)} frequency",
                description=f"Shows the frequency distribution of {category_column.name}.",
                priority=62,
                reason=f"{category_column.name} is a low-cardinality categorical column.",
                config={"aggregation": "count", "limit": 10},
            )
        )
        if category_column.unique_count <= 6:
            charts.append(
                make_chart(
                    chart_type="pie",
                    x=category_column.name,
                    y=None,
                    title=f"{title_case(category_column.name)} share",
                    description=f"Shows category share for {category_column.name}.",
                    priority=58,
                    reason=f"{category_column.name} has {category_column.unique_count} unique values.",
                    config={"aggregation": "count", "limit": 6},
                )
            )
    return charts


def recommend_heatmap(numeric_columns: list[ColumnProfile]) -> list[ChartSpec]:
    if len(numeric_columns) < 3:
        return []
    return [
        make_chart(
            chart_type="heatmap",
            x="numeric_columns",
            y="numeric_columns",
            title="Numeric correlation heatmap",
            description="Shows pairwise correlation strength across numeric columns.",
            priority=86,
            reason="At least three numeric columns were detected.",
            config={"method": "pearson", "limit": 20},
        )
    ]


def make_chart(
    chart_type: str,
    x: str,
    y: Optional[str],
    title: str,
    description: str,
    priority: int,
    reason: str,
    config: dict,
) -> ChartSpec:
    suffix = chart_type if y is None else f"{y}_{chart_type}"
    return ChartSpec(
        chart_id=slugify(f"{x}_{suffix}"),
        title=title,
        description=description,
        chart_type=chart_type,
        x=x,
        y=y,
        series=None,
        priority=max(0, min(100, int(priority))),
        reason=reason,
        config=config,
    )


def sort_and_limit_charts(charts: list[ChartSpec]) -> list[ChartSpec]:
    deduped: dict[str, ChartSpec] = {}
    for chart in charts:
        existing = deduped.get(chart.chart_id)
        if existing is None or chart.priority > existing.priority:
            deduped[chart.chart_id] = chart

    return sorted(deduped.values(), key=lambda chart: (-chart.priority, chart.chart_id))[
        :MAX_RECOMMENDED_CHARTS
    ]


def is_low_to_moderate_cardinality(column: ColumnProfile) -> bool:
    return column.unique_count <= 30 and column.unique_percent <= 80


def has_outliers(column: ColumnProfile) -> bool:
    q1 = column.stats.get("q1")
    q3 = column.stats.get("q3")
    min_value = column.stats.get("min")
    max_value = column.stats.get("max")
    if None in {q1, q3, min_value, max_value}:
        return False
    iqr = q3 - q1
    if iqr <= 0:
        return False
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return min_value < lower_bound or max_value > upper_bound


def appears_skewed(column: ColumnProfile) -> bool:
    mean = column.stats.get("mean")
    median = column.stats.get("median")
    std = column.stats.get("std")
    if mean is None or median is None or not std:
        return False
    return abs(mean - median) / std > 0.75


def is_trend_metric(column_name: str) -> bool:
    lower_name = column_name.lower()
    return any(hint in lower_name for hint in TREND_NAME_HINTS)


def is_additive_metric(column_name: str) -> bool:
    lower_name = column_name.lower()
    return any(hint in lower_name for hint in ("sales", "revenue", "profit", "amount", "total", "count"))


def title_case(value: str) -> str:
    return value.replace("_", " ").strip().title()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "chart"
