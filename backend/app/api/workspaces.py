from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import get_settings
from app.core.security import require_api_key
from app.core.user_auth import get_current_user_required
from app.db.models import User
from app.models.workspace_models import (
    WorkspaceCreateRequest,
    WorkspaceMemberResponse,
    WorkspaceMemberRoleUpdateRequest,
    WorkspaceMemberUpsertRequest,
    WorkspaceResponse,
)
from app.services.workspace_service import (
    WorkspaceNotFoundError,
    WorkspacePermissionError,
    WorkspaceValidationError,
    add_or_update_member,
    create_workspace,
    get_workspace,
    list_members,
    list_workspaces,
    remove_member,
    update_member_role,
)
from app.services.audit_service import record_event


router = APIRouter(prefix="/workspaces", tags=["workspaces"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[WorkspaceResponse])
def get_workspaces(current_user: Optional[User] = Depends(get_current_user_required)) -> list[WorkspaceResponse]:
    return list_workspaces(current_user)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace_route(
    payload: WorkspaceCreateRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> WorkspaceResponse:
    if not get_settings().user_auth_enabled or current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    workspace = create_workspace(payload, current_user)
    record_event(
        "workspace.create",
        "create",
        "success",
        actor_user_id=current_user.id,
        workspace_id=workspace.id,
        target_type="workspace",
        target_id=str(workspace.id),
        metadata={"name": workspace.name},
        request=request,
    )
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace_route(
    workspace_id: int,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> WorkspaceResponse:
    try:
        return get_workspace(workspace_id, current_user)
    except WorkspaceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
def get_workspace_members(
    workspace_id: int,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> list[WorkspaceMemberResponse]:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    try:
        return list_members(workspace_id, current_user)
    except WorkspaceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except WorkspacePermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse)
def add_workspace_member(
    workspace_id: int,
    payload: WorkspaceMemberUpsertRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> WorkspaceMemberResponse:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    try:
        member = add_or_update_member(workspace_id, payload, current_user)
        record_event(
            "workspace.member.add",
            "member_upsert",
            "success",
            actor_user_id=current_user.id,
            workspace_id=workspace_id,
            target_type="user",
            target_id=str(member.user_id),
            metadata={"role": member.role, "email": str(member.email)},
            request=request,
        )
        return member
    except WorkspaceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except WorkspacePermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except WorkspaceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
def update_workspace_member(
    workspace_id: int,
    user_id: int,
    payload: WorkspaceMemberRoleUpdateRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> WorkspaceMemberResponse:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    try:
        member = update_member_role(workspace_id, user_id, payload, current_user)
        record_event(
            "workspace.member.update",
            "member_update",
            "success",
            actor_user_id=current_user.id,
            workspace_id=workspace_id,
            target_type="user",
            target_id=str(user_id),
            metadata={"role": member.role},
            request=request,
        )
        return member
    except WorkspaceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except WorkspacePermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except WorkspaceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_200_OK)
def delete_workspace_member(
    workspace_id: int,
    user_id: int,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_required),
) -> dict[str, bool]:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    try:
        remove_member(workspace_id, user_id, current_user)
        record_event(
            "workspace.member.remove",
            "member_remove",
            "success",
            actor_user_id=current_user.id,
            workspace_id=workspace_id,
            target_type="user",
            target_id=str(user_id),
            request=request,
        )
        return {"deleted": True}
    except WorkspaceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except WorkspacePermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except WorkspaceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
