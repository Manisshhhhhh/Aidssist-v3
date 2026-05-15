from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.core.errors import not_found
from app.core.permissions import require_dataset_role
from app.core.rate_limit import rate_limited
from app.core.security import require_api_key
from app.db.models import User
from app.models.analysis_models import AnalysisResult
from app.models.job_models import JobCreateResponse
from app.repositories.dataset_repository import get_dataset_record
from app.services.job_service import enqueue_job
from app.services.audit_service import record_event
from app.services.analysis_service import (
    AnalysisReadError,
    DatasetNotFoundError,
    analyze_dataset,
)


router = APIRouter(tags=["analysis"], dependencies=[Depends(require_api_key)])


@router.post("/datasets/{dataset_id}/analyze", response_model=Union[AnalysisResult, JobCreateResponse])
def analyze_dataset_route(
    dataset_id: str,
    response: Response,
    request: Request,
    async_job: bool = Query(default=False, alias="async"),
    _: None = Depends(rate_limited),
    current_user: Optional[User] = Depends(require_dataset_role("editor")),
) -> Union[AnalysisResult, JobCreateResponse]:
    if async_job:
        record = get_dataset_record(dataset_id)
        if record is None:
            raise not_found(f"Dataset '{dataset_id}' was not found.")
        response.status_code = status.HTTP_202_ACCEPTED
        job = enqueue_job(
            job_type="analysis",
            input_payload={"dataset_id": dataset_id},
            workspace_id=record.workspace_id,
            dataset_id=dataset_id,
            current_user=current_user,
        )
        record_event(
            "analysis.run",
            "enqueue",
            "success",
            actor_user_id=current_user.id if current_user else None,
            workspace_id=record.workspace_id,
            dataset_id=dataset_id,
            job_id=job.job_id,
            request=request,
        )
        return job
    try:
        result = analyze_dataset(dataset_id)
        record = get_dataset_record(dataset_id)
        record_event(
            "analysis.run",
            "run",
            "success",
            actor_user_id=current_user.id if current_user else None,
            workspace_id=record.workspace_id if record else None,
            dataset_id=dataset_id,
            metadata={"row_count": result.row_count, "column_count": result.column_count},
            request=request,
        )
        return result
    except DatasetNotFoundError as exc:
        record_event("analysis.run", "run", "failure", dataset_id=dataset_id, metadata={"reason": str(exc)}, request=request)
        raise not_found(str(exc)) from exc
    except AnalysisReadError as exc:
        record_event("analysis.run", "run", "failure", dataset_id=dataset_id, metadata={"reason": str(exc)}, request=request)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
