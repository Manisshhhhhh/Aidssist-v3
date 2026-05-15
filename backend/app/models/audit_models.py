from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel


AuditOutcome = Literal["success", "failure", "denied"]


class AuditEventResponse(BaseModel):
    audit_id: str
    event_type: str
    actor_user_id: Optional[int]
    workspace_id: Optional[int]
    dataset_id: Optional[str]
    artifact_id: Optional[str]
    job_id: Optional[str]
    target_type: Optional[str]
    target_id: Optional[str]
    action: str
    outcome: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    metadata: dict[str, Any]
    created_at: datetime


class AuditEventListResponse(BaseModel):
    events: list[AuditEventResponse]
    limit: int
    offset: int
