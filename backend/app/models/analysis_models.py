from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    semantic_type: str
    missing_count: int
    missing_percent: float
    unique_count: int
    unique_percent: float
    sample_values: list[Any]
    stats: dict[str, Any]


class DataQuality(BaseModel):
    missing_cells: int
    missing_percent: float
    duplicate_rows: int
    duplicate_percent: float
    empty_columns: list[str]
    constant_columns: list[str]
    quality_score: int


class CorrelationResult(BaseModel):
    column_a: str
    column_b: str
    correlation: float


class ChartSpec(BaseModel):
    chart_id: str
    title: str
    description: str
    chart_type: str
    x: str
    y: Any = None
    series: Any = None
    priority: int
    reason: str
    config: dict[str, Any]


class Insight(BaseModel):
    type: str
    severity: str
    title: str
    message: str
    columns: list[str]


class AnalysisResult(BaseModel):
    dataset_id: str
    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    quality: DataQuality
    correlations: list[CorrelationResult]
    recommended_charts: list[ChartSpec]
    insights: list[Insight]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
