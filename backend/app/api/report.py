from __future__ import annotations

from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse

from app.core.errors import not_found
from app.core.permissions import require_dataset_role
from app.core.rate_limit import rate_limited
from app.core.security import require_api_key
from app.db.models import User
from app.models.job_models import JobCreateResponse
from app.models.report_models import ReportRequest, ReportResponse
from app.repositories.dataset_repository import get_dataset_record
from app.services.audit_service import record_event
from app.services.job_service import enqueue_job
from app.services.report_service import (
    ReportDatasetNotFoundError,
    ReportNotFoundError,
    ReportValidationError,
    generate_report,
    get_report_file,
)


router = APIRouter(tags=["report"], dependencies=[Depends(require_api_key)])


@router.post("/datasets/{dataset_id}/report", response_model=Union[ReportResponse, JobCreateResponse])
def create_report(
    dataset_id: str,
    report_request: ReportRequest,
    response: Response,
    request: Request,
    async_job: bool = Query(default=False, alias="async"),
    _: None = Depends(rate_limited),
    current_user: Optional[User] = Depends(require_dataset_role("editor")),
) -> Union[ReportResponse, JobCreateResponse]:
    if async_job:
        record = get_dataset_record(dataset_id)
        if record is None:
            raise not_found(f"Dataset '{dataset_id}' was not found.")
        response.status_code = status.HTTP_202_ACCEPTED
        job = enqueue_job(
            job_type="report",
            input_payload={"dataset_id": dataset_id, "request": report_request.model_dump(mode="json")},
            workspace_id=record.workspace_id,
            dataset_id=dataset_id,
            current_user=current_user,
        )
        record_event(
            "report.generate",
            "enqueue",
            "success",
            actor_user_id=current_user.id if current_user else None,
            workspace_id=record.workspace_id,
            dataset_id=dataset_id,
            job_id=job.job_id,
            metadata={"format": report_request.format},
            request=request,
        )
        return job
    try:
        result = generate_report(dataset_id, report_request, current_user=current_user, audit_request=request)
        record = get_dataset_record(dataset_id)
        record_event(
            "report.generate",
            "generate",
            "success",
            actor_user_id=current_user.id if current_user else None,
            workspace_id=record.workspace_id if record else None,
            dataset_id=dataset_id,
            target_type="report",
            target_id=result.report_id,
            metadata={"format": result.format, "filename": result.filename},
            request=request,
        )
        return result
    except ReportDatasetNotFoundError as exc:
        record_event("report.generate", "generate", "failure", dataset_id=dataset_id, metadata={"reason": str(exc)}, request=request)
        raise not_found(str(exc)) from exc
    except ReportValidationError as exc:
        record_event("report.generate", "generate", "failure", dataset_id=dataset_id, metadata={"reason": str(exc)}, request=request)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/datasets/{dataset_id}/reports/{report_id}/download")
def download_report(
    dataset_id: str,
    report_id: str,
    request: Request,
    format: Optional[str] = Query(default=None),
    current_user: Optional[User] = Depends(require_dataset_role("viewer")),
) -> FileResponse:
    try:
        report_file, media_type, filename = get_report_file(dataset_id, report_id, format)
    except (ReportDatasetNotFoundError, ReportNotFoundError) as exc:
        raise not_found(str(exc)) from exc

    record = get_dataset_record(dataset_id)
    record_event(
        "report.download",
        "download",
        "success",
        actor_user_id=current_user.id if current_user else None,
        workspace_id=record.workspace_id if record else None,
        dataset_id=dataset_id,
        target_type="report",
        target_id=report_id,
        metadata={"format": format, "filename": filename},
        request=request,
    )
    return FileResponse(path=report_file, media_type=media_type, filename=filename)
