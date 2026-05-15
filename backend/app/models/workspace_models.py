from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


WorkspaceRole = Literal["owner", "admin", "editor", "viewer"]


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    slug: str
    owner_user_id: Optional[int] = None
    current_user_role: Optional[WorkspaceRole] = None
    created_at: datetime
    updated_at: datetime


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceMemberResponse(BaseModel):
    user_id: int
    email: EmailStr
    full_name: str
    role: WorkspaceRole
    created_at: datetime
    updated_at: datetime


class WorkspaceMemberUpsertRequest(BaseModel):
    email: EmailStr
    role: WorkspaceRole


class WorkspaceMemberRoleUpdateRequest(BaseModel):
    role: WorkspaceRole
