from __future__ import annotations

from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, Response

from app.core.permissions import require_dataset_role
from app.core.security import require_api_key
from app.core.user_auth import get_current_user_required
from app.db.models import User
from app.models.artifact_models import DatasetArtifactsResponse
from app.services import storage_service
from app.services.audit_service import record_event
from app.services.artifact_service import ArtifactNotFoundError, get_artifact_for_download, list_dataset_artifacts


router = APIRouter(tags=["artifacts"], dependencies=[Depends(require_api_key)])


@router.get("/datasets/{dataset_id}/artifacts", response_model=DatasetArtifactsResponse)
def list_dataset_artifacts_route(
    dataset_id: str,
    _: object = Depends(require_dataset_role("viewer")),
) -> DatasetArtifactsResponse:
    return DatasetArtifactsResponse(artifacts=list_dataset_artifacts(dataset_id))


@router.get("/artifacts/{artifact_id}/download", response_model=None)
def download_artifact(
    artifact_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_required),
):
    try:
        record, local_path = get_artifact_for_download(artifact_id, current_user)
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    media_type = record.content_type or "application/octet-stream"
    record_event(
        "artifact.download",
        "download",
        "success",
        actor_user_id=current_user.id if current_user else None,
        workspace_id=record.workspace_id,
        dataset_id=record.dataset_id,
        artifact_id=record.artifact_id,
        target_type="artifact",
        target_id=record.artifact_id,
        metadata={"artifact_type": record.artifact_type, "filename": record.filename},
        request=request,
    )
    if local_path is not None:
        return FileResponse(path=local_path, media_type=media_type, filename=record.filename)

    return Response(
        content=storage_service.get_provider().read_bytes(record.storage_key),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{record.filename}"'},
    )
