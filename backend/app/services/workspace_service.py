from __future__ import annotations

from app.db.models import User, Workspace
from app.models.workspace_models import (
    WorkspaceCreateRequest,
    WorkspaceMemberResponse,
    WorkspaceMemberRoleUpdateRequest,
    WorkspaceMemberUpsertRequest,
    WorkspaceResponse,
    WorkspaceRole,
)
from app.repositories import user_repository, workspace_repository


class WorkspaceNotFoundError(Exception):
    """Raised when a workspace does not exist or is not visible."""


class WorkspacePermissionError(Exception):
    """Raised when a user lacks permission for a workspace action."""


class WorkspaceValidationError(Exception):
    """Raised when a workspace operation is invalid."""


def list_workspaces(current_user: User | None) -> list[WorkspaceResponse]:
    workspaces = workspace_repository.list_workspaces_for_user(current_user)
    return [workspace_response(workspace, current_user) for workspace in workspaces]


def create_workspace(request: WorkspaceCreateRequest, current_user: User) -> WorkspaceResponse:
    workspace = workspace_repository.create_workspace(request.name, current_user.id)
    return workspace_response(workspace, current_user)


def get_workspace(workspace_id: int, current_user: User | None) -> WorkspaceResponse:
    workspace = workspace_repository.get_workspace(workspace_id)
    if workspace is None or not can_access_workspace(workspace_id, current_user, "viewer"):
        raise WorkspaceNotFoundError("Workspace was not found.")
    return workspace_response(workspace, current_user)


def list_members(workspace_id: int, current_user: User) -> list[WorkspaceMemberResponse]:
    require_workspace_role(workspace_id, current_user, "admin")
    return [member_response(member, user) for member, user in workspace_repository.list_members(workspace_id)]


def add_or_update_member(
    workspace_id: int,
    request: WorkspaceMemberUpsertRequest,
    current_user: User,
) -> WorkspaceMemberResponse:
    require_workspace_role(workspace_id, current_user, "admin")
    target_user = user_repository.get_user_by_email(str(request.email).lower())
    if target_user is None:
        raise WorkspaceValidationError("User must register before being added to a workspace.")
    if request.role == "owner" and not has_workspace_role(workspace_id, current_user, "owner"):
        raise WorkspacePermissionError("Only workspace owners can add another owner.")

    member = workspace_repository.upsert_member(workspace_id, target_user.id, request.role)
    return member_response(member, target_user)


def update_member_role(
    workspace_id: int,
    user_id: int,
    request: WorkspaceMemberRoleUpdateRequest,
    current_user: User,
) -> WorkspaceMemberResponse:
    require_workspace_role(workspace_id, current_user, "admin")
    member = workspace_repository.get_membership(workspace_id, user_id)
    if member is None:
        raise WorkspaceNotFoundError("Workspace member was not found.")
    if (member.role == "owner" or request.role == "owner") and not has_workspace_role(workspace_id, current_user, "owner"):
        raise WorkspacePermissionError("Only owners can change owner memberships.")
    if member.role == "owner" and request.role != "owner" and workspace_repository.owner_count(workspace_id) <= 1:
        raise WorkspaceValidationError("Cannot demote the last workspace owner.")

    updated = workspace_repository.upsert_member(workspace_id, user_id, request.role)
    user = user_repository.get_user_by_id(user_id)
    if user is None:
        raise WorkspaceNotFoundError("Workspace member was not found.")
    return member_response(updated, user)


def remove_member(workspace_id: int, user_id: int, current_user: User) -> None:
    member = workspace_repository.get_membership(workspace_id, user_id)
    if member is None:
        raise WorkspaceNotFoundError("Workspace member was not found.")
    if current_user.id != user_id:
        require_workspace_role(workspace_id, current_user, "admin")
    if member.role == "owner" and workspace_repository.owner_count(workspace_id) <= 1:
        raise WorkspaceValidationError("Cannot remove the last workspace owner.")
    workspace_repository.delete_member(workspace_id, user_id)


def can_access_workspace(workspace_id: int, current_user: User | None, minimum_role: WorkspaceRole) -> bool:
    if current_user is None:
        return workspace_repository.get_workspace(workspace_id) is not None
    if current_user.is_admin:
        return True
    return has_workspace_role(workspace_id, current_user, minimum_role)


def has_workspace_role(workspace_id: int, current_user: User, minimum_role: WorkspaceRole) -> bool:
    membership = workspace_repository.get_membership(workspace_id, current_user.id)
    return bool(membership and workspace_repository.role_at_least(membership.role, minimum_role))


def require_workspace_role(workspace_id: int, current_user: User, minimum_role: WorkspaceRole) -> None:
    workspace = workspace_repository.get_workspace(workspace_id)
    if workspace is None:
        raise WorkspaceNotFoundError("Workspace was not found.")
    if current_user.is_admin:
        return
    if not has_workspace_role(workspace_id, current_user, minimum_role):
        raise WorkspacePermissionError("You do not have permission for this workspace action.")


def workspace_response(workspace: Workspace, current_user: User | None) -> WorkspaceResponse:
    role = None
    if current_user is not None:
        membership = workspace_repository.get_membership(workspace.id, current_user.id)
        role = "owner" if current_user.is_admin and membership is None else (membership.role if membership else None)
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        owner_user_id=workspace.owner_user_id,
        current_user_role=role,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


def member_response(member, user: User) -> WorkspaceMemberResponse:
    return WorkspaceMemberResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=member.role,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )
