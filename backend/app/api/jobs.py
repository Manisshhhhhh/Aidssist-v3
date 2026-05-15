from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import require_api_key
from app.core.user_auth import get_current_user_required
from app.db.models import User
from app.models.job_models import JobListResponse, JobResponse, JobStatus, JobType
from app.services.job_service import (
    JobNotFoundError,
    JobPermissionError,
    JobValidationError,
    cancel_visible_job,
    get_visible_job,
    list_visible_jobs,
)


router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=JobListResponse)
def list_jobs_route(
    workspace_id: Optional[int] = Query(default=None),
    status_filter: Optional[JobStatus] = Query(default=None, alias="status"),
    job_type: Optional[JobType] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_required),
) -> JobListResponse:
    return JobListResponse(
        jobs=list_visible_jobs(
            current_user=current_user,
            workspace_id=workspace_id,
            status=status_filter,
            job_type=job_type,
            limit=limit,
        )
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job_route(
    job_id: str,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> JobResponse:
    try:
        return get_visible_job(job_id, current_user)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{job_id}/cancel", response_model=JobResponse)
def cancel_job_route(
    job_id: str,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> JobResponse:
    try:
        return cancel_visible_job(job_id, current_user)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except JobPermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except JobValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
