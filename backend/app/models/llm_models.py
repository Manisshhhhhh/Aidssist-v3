from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


AiSummaryTone = Literal["executive", "analyst", "concise"]
AiSummaryFormat = Literal["bullets", "narrative"]


class AiSummaryRequest(BaseModel):
    include_forecast: bool = True
    include_charts: bool = True
    tone: AiSummaryTone = "executive"
    format: AiSummaryFormat = "bullets"


class AiSummaryGrounding(BaseModel):
    used_analysis: bool
    used_forecast: bool
    used_charts: bool
    raw_rows_sent: bool = False


class AiSummaryResponse(BaseModel):
    dataset_id: str
    summary_id: str
    provider: str
    model: str
    summary: str
    grounding: AiSummaryGrounding
    warnings: list[str]
    created_at: datetime
