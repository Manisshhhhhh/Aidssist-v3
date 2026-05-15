from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import JobRecord
from app.db.session import new_session
from app.models.job_models import JobResponse, JobStatus, JobType


TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}


def create_job(
    job_type: JobType,
    input_payload: dict[str, Any],
    workspace_id: int | None = None,
    dataset_id: str | None = None,
    created_by_user_id: int | None = None,
) -> JobRecord:
    session = new_session()
    try:
        record = create_job_with_session(
            session=session,
            job_type=job_type,
            input_payload=input_payload,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            created_by_user_id=created_by_user_id,
        )
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def create_job_with_session(
    session: Session,
    job_type: JobType,
    input_payload: dict[str, Any],
    workspace_id: int | None = None,
    dataset_id: str | None = None,
    created_by_user_id: int | None = None,
) -> JobRecord:
    now = datetime.now(timezone.utc)
    record = JobRecord(
        job_id=str(uuid4()),
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        created_by_user_id=created_by_user_id,
        job_type=job_type,
        status="queued",
        progress=0,
        input_json=json.dumps(json_safe(input_payload), ensure_ascii=False),
        output_json=None,
        error_message=None,
        attempts=0,
        max_attempts=get_settings().job_max_attempts,
        created_at=now,
        updated_at=now,
    )
    session.add(record)
    return record


def get_job(job_id: str) -> JobRecord | None:
    session = new_session()
    try:
        return session.query(JobRecord).filter(JobRecord.job_id == job_id).one_or_none()
    finally:
        session.close()


def list_jobs(
    workspace_ids: list[int] | None = None,
    created_by_user_id: int | None = None,
    workspace_id: int | None = None,
    status: str | None = None,
    job_type: str | None = None,
    limit: int = 50,
    include_all: bool = False,
) -> list[JobRecord]:
    session = new_session()
    try:
        query = session.query(JobRecord)
        if not include_all:
            if workspace_id is not None:
                query = query.filter(JobRecord.workspace_id == workspace_id)
            elif workspace_ids is not None:
                if not workspace_ids:
                    return []
                query = query.filter(JobRecord.workspace_id.in_(workspace_ids))
            elif created_by_user_id is not None:
                query = query.filter(JobRecord.created_by_user_id == created_by_user_id)
        if status:
            query = query.filter(JobRecord.status == status)
        if job_type:
            query = query.filter(JobRecord.job_type == job_type)
        return query.order_by(JobRecord.created_at.desc(), JobRecord.id.desc()).limit(limit).all()
    finally:
        session.close()


def claim_next_queued_job() -> JobRecord | None:
    session = new_session()
    try:
        record = (
            session.query(JobRecord)
            .filter(JobRecord.status == "queued")
            .order_by(JobRecord.created_at.asc(), JobRecord.id.asc())
            .with_for_update(nowait=False)
            .first()
        )
        if record is None:
            return None
        now = datetime.now(timezone.utc)
        record.status = "running"
        record.progress = max(record.progress, 5)
        record.attempts += 1
        record.started_at = now
        record.updated_at = now
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def update_progress(job_id: str, progress: int) -> JobRecord | None:
    session = new_session()
    try:
        record = session.query(JobRecord).filter(JobRecord.job_id == job_id).one_or_none()
        if record is None:
            return None
        record.progress = min(100, max(0, progress))
        record.updated_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def mark_succeeded(job_id: str, output_payload: dict[str, Any]) -> JobRecord | None:
    return update_terminal_job(job_id, "succeeded", output_payload=output_payload, error_message=None)


def mark_failed(job_id: str, error_message: str) -> JobRecord | None:
    return update_terminal_job(job_id, "failed", output_payload=None, error_message=sanitize_error(error_message))


def cancel_job(job_id: str) -> JobRecord | None:
    session = new_session()
    try:
        record = session.query(JobRecord).filter(JobRecord.job_id == job_id).one_or_none()
        if record is None:
            return None
        if record.status != "queued":
            return record
        now = datetime.now(timezone.utc)
        record.status = "cancelled"
        record.progress = 100
        record.finished_at = now
        record.updated_at = now
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def update_terminal_job(
    job_id: str,
    status: JobStatus,
    output_payload: dict[str, Any] | None,
    error_message: str | None,
) -> JobRecord | None:
    session = new_session()
    try:
        record = session.query(JobRecord).filter(JobRecord.job_id == job_id).one_or_none()
        if record is None:
            return None
        now = datetime.now(timezone.utc)
        record.status = status
        record.progress = 100
        record.output_json = json.dumps(json_safe(output_payload), ensure_ascii=False) if output_payload is not None else None
        record.error_message = error_message
        record.finished_at = now
        record.updated_at = now
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def job_to_response(record: JobRecord) -> JobResponse:
    output = None
    if record.output_json:
        try:
            output = json.loads(record.output_json)
        except json.JSONDecodeError:
            output = None
    return JobResponse(
        job_id=record.job_id,
        job_type=record.job_type,
        status=record.status,
        progress=record.progress,
        dataset_id=record.dataset_id,
        workspace_id=record.workspace_id,
        output=output,
        error_message=record.error_message,
        attempts=record.attempts,
        max_attempts=record.max_attempts,
        created_at=record.created_at,
        started_at=record.started_at,
        finished_at=record.finished_at,
    )


def load_input(record: JobRecord) -> dict[str, Any]:
    if not record.input_json:
        return {}
    try:
        payload = json.loads(record.input_json)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def sanitize_error(message: str) -> str:
    compact = " ".join(message.split())
    return compact[:500] or "Job failed."


def json_safe(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        if value != value or value in {float("inf"), float("-inf")}:
            return None
        return value
    return str(value)
