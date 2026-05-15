from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status

from app.core.config import get_settings
from app.core.user_auth import get_current_user_required
from app.db.models import User
from app.models.workspace_models import WorkspaceRole
from app.repositories.dataset_repository import get_dataset_record
from app.repositories.workspace_repository import get_or_create_default_workspace
from app.services.workspace_service import can_access_workspace


def require_dataset_role(minimum_role: WorkspaceRole):
    def dependency(
        dataset_id: str,
        current_user: Optional[User] = Depends(get_current_user_required),
    ) -> Optional[User]:
        if not get_settings().user_auth_enabled:
            return None
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")

        record = get_dataset_record(dataset_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' was not found.")
        if can_access_workspace(record.workspace_id, current_user, minimum_role):
            return current_user
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset '{dataset_id}' was not found.")

    return dependency


def require_workspace_role(minimum_role: WorkspaceRole):
    def dependency(
        workspace_id: Optional[int] = None,
        current_user: Optional[User] = Depends(get_current_user_required),
    ) -> Optional[User]:
        if not get_settings().user_auth_enabled:
            return None
        if current_user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
        if workspace_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="workspace_id is required.")
        if can_access_workspace(workspace_id, current_user, minimum_role):
            return current_user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission for this workspace.")

    return dependency


def resolve_upload_workspace_id(workspace_id: Optional[int], current_user: Optional[User]) -> int:
    if not get_settings().user_auth_enabled:
        return get_or_create_default_workspace().id
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")

    if workspace_id is None:
        workspaces = current_user_workspaces(current_user)
        if not workspaces:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No workspace is available for this user.")
        workspace_id = workspaces[0].id

    if can_access_workspace(workspace_id, current_user, "editor"):
        return workspace_id
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You need editor access to upload to this workspace.")


def current_user_workspaces(current_user: User):
    from app.repositories.workspace_repository import list_workspaces_for_user

    return list_workspaces_for_user(current_user)
