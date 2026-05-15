from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import require_api_key
from app.core.user_auth import get_current_user_required
from app.db.models import User
from app.models.audit_models import AuditEventListResponse, AuditEventResponse
from app.services.audit_service import get_visible_event, list_visible_events


router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(require_api_key)])


@router.get("/events", response_model=AuditEventListResponse)
def list_audit_events(
    workspace_id: Optional[int] = Query(default=None),
    dataset_id: Optional[str] = Query(default=None),
    actor_user_id: Optional[int] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    outcome: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: Optional[User] = Depends(get_current_user_required),
) -> AuditEventListResponse:
    return AuditEventListResponse(
        events=list_visible_events(
            current_user=current_user,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            outcome=outcome,
            limit=limit,
            offset=offset,
        ),
        limit=limit,
        offset=offset,
    )


@router.get("/events/{audit_id}", response_model=AuditEventResponse)
def get_audit_event(
    audit_id: str,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> AuditEventResponse:
    event = get_visible_event(audit_id, current_user)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit event was not found.")
    return event
