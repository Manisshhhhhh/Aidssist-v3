from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    conversation_id: Optional[str] = None


class ChatResult(BaseModel):
    type: str
    data: Any = None


class ChatResponse(BaseModel):
    dataset_id: str
    conversation_id: str
    message: str
    answer: str
    intent: str
    confidence: float
    columns_used: list[str]
    result: ChatResult
    suggested_followups: list[str]
    warnings: list[str]
    created_at: datetime
