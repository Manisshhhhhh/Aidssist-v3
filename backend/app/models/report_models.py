from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ReportRequest(BaseModel):
    format: Literal["html", "json"] = "html"
    include_forecast: bool = True
    include_charts: bool = True
    include_chat_summary: bool = False
    include_ai_summary: bool = False


class ReportResponse(BaseModel):
    dataset_id: str
    report_id: str
    format: Literal["html", "json"]
    filename: str
    download_url: str
    created_at: datetime
