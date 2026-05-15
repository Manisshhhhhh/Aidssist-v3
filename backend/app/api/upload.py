from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status

from app.core.permissions import resolve_upload_workspace_id
from app.core.rate_limit import rate_limited
from app.core.security import require_api_key
from app.core.user_auth import get_current_user_required
from app.db.models import User
from app.models.dataset_models import DatasetMetadata
from app.services.dataset_service import DatasetValidationError, create_dataset_from_upload
from app.services.audit_service import record_event


router = APIRouter(tags=["upload"], dependencies=[Depends(require_api_key)])


@router.post("/upload", response_model=DatasetMetadata, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
    workspace_id: Optional[int] = Query(default=None),
    _: None = Depends(rate_limited),
    current_user: Optional[User] = Depends(get_current_user_required),
) -> DatasetMetadata:
    try:
        target_workspace_id = resolve_upload_workspace_id(workspace_id, current_user)
        metadata = await create_dataset_from_upload(
            file,
            owner_user_id=current_user.id if current_user else None,
            workspace_id=target_workspace_id,
        )
        record_event(
            "dataset.upload",
            "upload",
            "success",
            actor_user_id=current_user.id if current_user else None,
            workspace_id=target_workspace_id,
            dataset_id=metadata.dataset_id,
            metadata={
                "original_filename": metadata.original_filename,
                "file_size_bytes": metadata.file_size_bytes,
                "row_count": metadata.row_count,
                "column_count": metadata.column_count,
            },
            request=request,
        )
        return metadata
    except DatasetValidationError as exc:
        record_event(
            "dataset.upload",
            "upload",
            "failure",
            actor_user_id=current_user.id if current_user else None,
            workspace_id=workspace_id,
            metadata={"reason": str(exc)},
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
