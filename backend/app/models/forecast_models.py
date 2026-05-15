from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    date_column: str
    target_column: str
    periods: int = Field(default=12, ge=1, le=365)
    frequency: Literal["auto", "D", "W", "M"] = "auto"
    model: Literal["auto", "linear_regression", "moving_average"] = "auto"


class HistoricalPoint(BaseModel):
    date: str
    value: float


class ForecastPoint(BaseModel):
    date: str
    predicted_value: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class ForecastMetrics(BaseModel):
    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None


class ForecastResponse(BaseModel):
    dataset_id: str
    date_column: str
    target_column: str
    model_used: str
    frequency: str
    periods: int
    historical_points: list[HistoricalPoint]
    forecast_points: list[ForecastPoint]
    metrics: ForecastMetrics
    assumptions: list[str]
    warnings: list[str]
    created_at: datetime
