from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.api.diagnostics import ensure_admin_or_local
from app.core.security import require_api_key
from app.core.user_auth import get_current_user_required
from app.db.models import User
from app.models.backup_models import BackupListResponse, BackupRequest, BackupResponse
from app.services.audit_service import record_event
from app.services.backup_service import BackupError, create_backup, get_backup_path, list_backups


router = APIRouter(prefix="/backups", tags=["backups"], dependencies=[Depends(require_api_key)])


@router.post("", response_model=BackupResponse, status_code=status.HTTP_201_CREATED)
def create_backup_route(
    payload: BackupRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> BackupResponse:
    ensure_admin_or_local(current_user)
    backup = create_backup(payload)
    record_event(
        "backup.create",
        "create",
        "success",
        actor_user_id=current_user.id if current_user else None,
        metadata={"backup_id": backup.backup_id, "size_bytes": backup.size_bytes},
        request=request,
    )
    return backup


@router.get("", response_model=BackupListResponse)
def list_backups_route(current_user: Optional[User] = Depends(get_current_user_required)) -> BackupListResponse:
    ensure_admin_or_local(current_user)
    return BackupListResponse(backups=list_backups())


@router.get("/{backup_id}/download")
def download_backup_route(
    backup_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_required),
):
    ensure_admin_or_local(current_user)
    try:
        path = get_backup_path(backup_id)
    except BackupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    record_event(
        "backup.download",
        "download",
        "success",
        actor_user_id=current_user.id if current_user else None,
        target_type="backup",
        target_id=backup_id,
        request=request,
    )
    return FileResponse(path=path, media_type="application/zip", filename=path.name)
