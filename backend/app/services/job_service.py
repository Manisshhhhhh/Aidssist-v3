from __future__ import annotations

from typing import Optional

from app.db.models import JobRecord, User
from app.models.job_models import JobCreateResponse, JobResponse, JobStatus, JobType
from app.repositories import job_repository
from app.repositories.workspace_repository import list_workspaces_for_user
from app.services.audit_service import record_event
from app.services.workspace_service import can_access_workspace


class JobNotFoundError(Exception):
    """Raised when a job is not visible or does not exist."""


class JobPermissionError(Exception):
    """Raised when a user cannot mutate a job."""


class JobValidationError(Exception):
    """Raised when a job action is invalid."""


def enqueue_job(
    job_type: JobType,
    input_payload: dict,
    workspace_id: int | None = None,
    dataset_id: str | None = None,
    current_user: Optional[User] = None,
) -> JobCreateResponse:
    record = job_repository.create_job(
        job_type=job_type,
        input_payload=input_payload,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        created_by_user_id=current_user.id if current_user else None,
    )
    record_event(
        "job.create",
        "create",
        "success",
        actor_user_id=current_user.id if current_user else None,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        job_id=record.job_id,
        target_type="job",
        target_id=record.job_id,
        metadata={"job_type": job_type},
    )
    return JobCreateResponse(
        job_id=record.job_id,
        job_type=record.job_type,
        status=record.status,
        progress=record.progress,
        status_url=f"/jobs/{record.job_id}",
        created_at=record.created_at,
    )


def get_visible_job(job_id: str, current_user: Optional[User]) -> JobResponse:
    record = job_repository.get_job(job_id)
    if record is None or not can_view_job(record, current_user):
        raise JobNotFoundError("Job was not found.")
    return job_repository.job_to_response(record)


def list_visible_jobs(
    current_user: Optional[User],
    workspace_id: int | None = None,
    status: JobStatus | None = None,
    job_type: JobType | None = None,
    limit: int = 50,
) -> list[JobResponse]:
    limit = min(100, max(1, limit))
    if current_user is None:
        records = job_repository.list_jobs(
            workspace_id=workspace_id,
            status=status,
            job_type=job_type,
            limit=limit,
            include_all=workspace_id is None,
        )
    elif current_user.is_admin:
        records = job_repository.list_jobs(
            workspace_id=workspace_id,
            status=status,
            job_type=job_type,
            limit=limit,
            include_all=workspace_id is None,
        )
    else:
        workspace_ids = [workspace.id for workspace in list_workspaces_for_user(current_user)]
        if workspace_id is not None:
            if workspace_id not in workspace_ids:
                return []
            workspace_ids = [workspace_id]
        records = job_repository.list_jobs(
            workspace_ids=workspace_ids,
            created_by_user_id=current_user.id,
            status=status,
            job_type=job_type,
            limit=limit,
        )
    return [job_repository.job_to_response(record) for record in records if can_view_job(record, current_user)]


def cancel_visible_job(job_id: str, current_user: Optional[User]) -> JobResponse:
    record = job_repository.get_job(job_id)
    if record is None or not can_view_job(record, current_user):
        raise JobNotFoundError("Job was not found.")
    if not can_cancel_job(record, current_user):
        raise JobPermissionError("You do not have permission to cancel this job.")
    if record.status != "queued":
        raise JobValidationError("Only queued jobs can be cancelled.")
    cancelled = job_repository.cancel_job(job_id)
    if cancelled is None:
        raise JobNotFoundError("Job was not found.")
    record_event(
        "job.cancelled",
        "cancel",
        "success",
        actor_user_id=current_user.id if current_user else None,
        workspace_id=cancelled.workspace_id,
        dataset_id=cancelled.dataset_id,
        job_id=cancelled.job_id,
        target_type="job",
        target_id=cancelled.job_id,
        metadata={"job_type": cancelled.job_type},
    )
    return job_repository.job_to_response(cancelled)


def can_view_job(record: JobRecord, current_user: Optional[User]) -> bool:
    if current_user is None:
        return True
    if current_user.is_admin:
        return True
    if record.created_by_user_id == current_user.id:
        return True
    if record.workspace_id is not None:
        return can_access_workspace(record.workspace_id, current_user, "viewer")
    return False


def can_cancel_job(record: JobRecord, current_user: Optional[User]) -> bool:
    if current_user is None:
        return True
    if current_user.is_admin:
        return True
    if record.created_by_user_id == current_user.id:
        return True
    if record.workspace_id is not None:
        return can_access_workspace(record.workspace_id, current_user, "admin")
    return False
