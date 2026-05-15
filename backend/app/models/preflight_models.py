from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


PreflightStatus = Literal["ok", "warning", "error"]


class PreflightCheck(BaseModel):
    name: str
    status: PreflightStatus
    message: str


class PreflightResponse(BaseModel):
    status: PreflightStatus
    checks: list[PreflightCheck]
    created_at: datetime
