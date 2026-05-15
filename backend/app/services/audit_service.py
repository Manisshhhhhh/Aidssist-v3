from __future__ import annotations

from typing import Any, Optional

from fastapi import Request

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.request_context import get_request_id
from app.db.models import AuditLogRecord, User
from app.models.audit_models import AuditEventResponse
from app.repositories import audit_repository
from app.repositories.workspace_repository import list_workspaces_for_user
from app.services.workspace_service import can_access_workspace


logger = get_logger(__name__)
SECRET_MARKERS = ("password", "token", "secret", "key", "authorization", "jwt", "credential")
MAX_METADATA_CHARS = 4000


def record_event(
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
    metadata: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    if not get_settings().audit_log_enabled:
        return
    try:
        audit_repository.create_event(
            event_type=event_type,
            action=action,
            outcome=outcome,
            actor_user_id=actor_user_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            artifact_id=artifact_id,
            job_id=job_id,
            target_type=target_type,
            target_id=target_id,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent")[:512] if request else None,
            request_id=get_request_id(),
            metadata=sanitize_metadata(metadata or {}),
        )
    except Exception:
        logger.exception("audit event could not be recorded", extra={"event_type": event_type, "outcome": outcome})


def sanitize_metadata(value: dict[str, Any]) -> dict[str, Any]:
    sanitized = _sanitize(value)
    if not isinstance(sanitized, dict):
        return {}
    text = str(sanitized)
    if len(text) <= MAX_METADATA_CHARS:
        return sanitized
    return {"truncated": True, "summary": text[:MAX_METADATA_CHARS]}


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if any(marker in key_text.lower() for marker in SECRET_MARKERS):
                clean[key_text] = "[redacted]"
            else:
                clean[key_text] = _sanitize(item)
        return clean
    if isinstance(value, list):
        return [_sanitize(item) for item in value[:20]]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value[:20]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, str) and len(value) > 500:
            return value[:500] + "..."
        return value
    return str(value)


def list_visible_events(
    current_user: Optional[User],
    workspace_id: Optional[int] = None,
    actor_user_id: Optional[int] = None,
    dataset_id: Optional[str] = None,
    event_type: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditEventResponse]:
    settings = get_settings()
    if not settings.user_auth_enabled or current_user is None:
        records = audit_repository.list_events(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            dataset_id=dataset_id,
            event_type=event_type,
            outcome=outcome,
            limit=limit,
            offset=offset,
            include_all=workspace_id is None and actor_user_id is None,
        )
        return [audit_repository.event_to_response(record) for record in records]

    if current_user.is_admin:
        records = audit_repository.list_events(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            dataset_id=dataset_id,
            event_type=event_type,
            outcome=outcome,
            limit=limit,
            offset=offset,
            include_all=workspace_id is None,
        )
        return [audit_repository.event_to_response(record) for record in records]

    if workspace_id is not None:
        if can_access_workspace(workspace_id, current_user, "admin"):
            records = audit_repository.list_events(
                workspace_id=workspace_id,
                actor_user_id=actor_user_id,
                dataset_id=dataset_id,
                event_type=event_type,
                outcome=outcome,
                limit=limit,
                offset=offset,
            )
        else:
            records = audit_repository.list_events(
                workspace_id=workspace_id,
                actor_user_id=current_user.id,
                dataset_id=dataset_id,
                event_type=event_type,
                outcome=outcome,
                limit=limit,
                offset=offset,
            )
        return [audit_repository.event_to_response(record) for record in records if can_view_event(record, current_user)]

    workspace_ids = [workspace.id for workspace in list_workspaces_for_user(current_user)]
    records = audit_repository.list_events(
        workspace_ids=workspace_ids,
        actor_user_id=actor_user_id,
        dataset_id=dataset_id,
        event_type=event_type,
        outcome=outcome,
        limit=limit,
        offset=offset,
    )
    return [audit_repository.event_to_response(record) for record in records if can_view_event(record, current_user)]


def get_visible_event(audit_id: str, current_user: Optional[User]) -> Optional[AuditEventResponse]:
    record = audit_repository.get_event(audit_id)
    if record is None or not can_view_event(record, current_user):
        return None
    return audit_repository.event_to_response(record)


def can_view_event(record: AuditLogRecord, current_user: Optional[User]) -> bool:
    if not get_settings().user_auth_enabled:
        return True
    if current_user is None:
        return False
    if current_user.is_admin:
        return True
    if record.actor_user_id == current_user.id:
        return True
    if record.workspace_id is not None and can_access_workspace(record.workspace_id, current_user, "admin"):
        return True
    return False
