from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.permissions import require_dataset_role
from app.core.rate_limit import rate_limited
from app.core.security import require_api_key
from app.db.models import User
from app.repositories.dataset_repository import get_dataset_record
from app.models.chat_models import ChatRequest, ChatResponse
from app.services.audit_service import record_event
from app.services.query_service import DatasetQueryError, DatasetQueryNotFoundError, answer_dataset_question


router = APIRouter(tags=["chat"], dependencies=[Depends(require_api_key)])


@router.post("/datasets/{dataset_id}/chat", response_model=ChatResponse)
def chat_with_dataset(
    dataset_id: str,
    chat_request: ChatRequest,
    request: Request,
    _: None = Depends(rate_limited),
    current_user: Optional[User] = Depends(require_dataset_role("viewer")),
) -> ChatResponse:
    try:
        response = answer_dataset_question(dataset_id, chat_request)
        record = get_dataset_record(dataset_id)
        record_event(
            "chat.ask",
            "ask",
            "success",
            actor_user_id=current_user.id if current_user else None,
            workspace_id=record.workspace_id if record else None,
            dataset_id=dataset_id,
            metadata={"intent": response.intent, "columns_used": response.columns_used},
            request=request,
        )
        return response
    except DatasetQueryNotFoundError as exc:
        record_event("chat.ask", "ask", "failure", dataset_id=dataset_id, metadata={"reason": str(exc)}, request=request)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DatasetQueryError as exc:
        record_event("chat.ask", "ask", "failure", dataset_id=dataset_id, metadata={"reason": str(exc)}, request=request)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
