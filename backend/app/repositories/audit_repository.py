from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from app.db.models import AuditLogRecord
from app.db.session import new_session
from app.models.audit_models import AuditEventResponse


def create_event(
    event_type: str,
    action: str,
    outcome: str,
    actor_user_id: Optional[int] = None,
    workspace_id: Optional[int] = None,
    dataset_id: Optional[str] = None,
    artifact_id: Optional[str] = None,
    job_id: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AuditLogRecord:
    session = new_session()
    try:
        record = AuditLogRecord(
            audit_id=str(uuid4()),
            event_type=event_type,
            actor_user_id=actor_user_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            artifact_id=artifact_id,
            job_id=job_id,
            target_type=target_type,
            target_id=target_id,
            action=action,
            outcome=outcome,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
            created_at=datetime.now(timezone.utc),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def get_event(audit_id: str) -> Optional[AuditLogRecord]:
    session = new_session()
    try:
        return session.query(AuditLogRecord).filter(AuditLogRecord.audit_id == audit_id).one_or_none()
    finally:
        session.close()


def list_events(
    workspace_id: Optional[int] = None,
    workspace_ids: Optional[list[int]] = None,
    actor_user_id: Optional[int] = None,
    dataset_id: Optional[str] = None,
    event_type: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    include_all: bool = False,
) -> list[AuditLogRecord]:
    session = new_session()
    try:
        query = session.query(AuditLogRecord)
        if not include_all:
            if workspace_id is not None:
                query = query.filter(AuditLogRecord.workspace_id == workspace_id)
            elif workspace_ids is not None:
                if not workspace_ids:
                    return []
                query = query.filter(AuditLogRecord.workspace_id.in_(workspace_ids))
            elif actor_user_id is not None:
                query = query.filter(AuditLogRecord.actor_user_id == actor_user_id)
        if actor_user_id is not None and (include_all or workspace_id is not None or workspace_ids is not None):
            query = query.filter(AuditLogRecord.actor_user_id == actor_user_id)
        if dataset_id:
            query = query.filter(AuditLogRecord.dataset_id == dataset_id)
        if event_type:
            query = query.filter(AuditLogRecord.event_type == event_type)
        if outcome:
            query = query.filter(AuditLogRecord.outcome == outcome)
        return (
            query.order_by(AuditLogRecord.created_at.desc(), AuditLogRecord.id.desc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 200)))
            .all()
        )
    finally:
        session.close()


def event_to_response(record: AuditLogRecord) -> AuditEventResponse:
    metadata: dict[str, Any] = {}
    if record.metadata_json:
        try:
            parsed = json.loads(record.metadata_json)
            if isinstance(parsed, dict):
                metadata = parsed
        except json.JSONDecodeError:
            metadata = {}
    return AuditEventResponse(
        audit_id=record.audit_id,
        event_type=record.event_type,
        actor_user_id=record.actor_user_id,
        workspace_id=record.workspace_id,
        dataset_id=record.dataset_id,
        artifact_id=record.artifact_id,
        job_id=record.job_id,
        target_type=record.target_type,
        target_id=record.target_id,
        action=record.action,
        outcome=record.outcome,
        ip_address=record.ip_address,
        user_agent=record.user_agent,
        request_id=record.request_id,
        metadata=metadata,
        created_at=record.created_at,
    )
