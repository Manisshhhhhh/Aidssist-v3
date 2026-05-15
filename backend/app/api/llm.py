from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.permissions import require_dataset_role
from app.core.security import require_api_key
from app.db.models import User
from app.models.llm_models import AiSummaryRequest, AiSummaryResponse
from app.services.llm_service import (
    AiSummaryDatasetNotFoundError,
    AiSummaryProviderError,
    AiSummaryUnavailableError,
    AiSummaryValidationError,
    create_ai_summary,
)


router = APIRouter(tags=["llm"], dependencies=[Depends(require_api_key)])


@router.post("/datasets/{dataset_id}/ai-summary", response_model=AiSummaryResponse)
def create_ai_summary_route(
    dataset_id: str,
    payload: AiSummaryRequest,
    request: Request,
    current_user: Optional[User] = Depends(require_dataset_role("viewer")),
) -> AiSummaryResponse:
    try:
        return create_ai_summary(dataset_id, payload, current_user=current_user, request=request)
    except AiSummaryDatasetNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AiSummaryValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except AiSummaryUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except AiSummaryProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
