from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ChartDataResponse(BaseModel):
    dataset_id: str
    chart_id: str
    title: str
    description: str
    chart_type: str
    x: str
    y: Any = None
    series: Any = None
    data: list[dict[str, Any]]
    metadata: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
