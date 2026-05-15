from __future__ import annotations

import re
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.init_db import DEFAULT_WORKSPACE_NAME, DEFAULT_WORKSPACE_SLUG
from app.db.models import User, Workspace, WorkspaceMember
from app.db.session import new_session


ROLE_ORDER = {"viewer": 1, "editor": 2, "admin": 3, "owner": 4}
WORKSPACE_ROLES = tuple(ROLE_ORDER.keys())


def get_or_create_default_workspace(session: Optional[Session] = None) -> Workspace:
    owns_session = session is None
    db = session or new_session()
    try:
        workspace = db.query(Workspace).filter(Workspace.slug == DEFAULT_WORKSPACE_SLUG).one_or_none()
        if workspace is None:
            workspace = Workspace(name=DEFAULT_WORKSPACE_NAME, slug=DEFAULT_WORKSPACE_SLUG)
            db.add(workspace)
            db.commit()
            db.refresh(workspace)
        return workspace
    finally:
        if owns_session:
            db.close()


def get_default_workspace() -> Optional[Workspace]:
    session = new_session()
    try:
        return session.query(Workspace).filter(Workspace.slug == DEFAULT_WORKSPACE_SLUG).one_or_none()
    finally:
        session.close()


def create_workspace(name: str, owner_user_id: int) -> Workspace:
    session = new_session()
    try:
        workspace = Workspace(name=name.strip(), slug=unique_slug(session, name), owner_user_id=owner_user_id)
        session.add(workspace)
        session.flush()
        session.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner_user_id, role="owner"))
        session.commit()
        session.refresh(workspace)
        return workspace
    finally:
        session.close()


def ensure_personal_workspace(user: User) -> Workspace:
    session = new_session()
    try:
        membership = (
            session.query(WorkspaceMember)
            .filter(WorkspaceMember.user_id == user.id, WorkspaceMember.role == "owner")
            .order_by(WorkspaceMember.id.asc())
            .first()
        )
        if membership is not None:
            return session.query(Workspace).filter(Workspace.id == membership.workspace_id).one()

        name = f"{user.full_name or user.email}'s Workspace"
        workspace = Workspace(name=name, slug=unique_slug(session, name), owner_user_id=user.id)
        session.add(workspace)
        session.flush()
        session.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
        session.commit()
        session.refresh(workspace)
        return workspace
    finally:
        session.close()


def list_workspaces_for_user(user: Optional[User]) -> list[Workspace]:
    session = new_session()
    try:
        if user is None:
            workspace = session.query(Workspace).filter(Workspace.slug == DEFAULT_WORKSPACE_SLUG).one_or_none()
            return [workspace] if workspace else []
        if user.is_admin:
            return session.query(Workspace).order_by(Workspace.created_at.asc(), Workspace.id.asc()).all()
        return (
            session.query(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .filter(WorkspaceMember.user_id == user.id)
            .order_by(Workspace.created_at.asc(), Workspace.id.asc())
            .all()
        )
    finally:
        session.close()


def get_workspace(workspace_id: int) -> Optional[Workspace]:
    session = new_session()
    try:
        return session.query(Workspace).filter(Workspace.id == workspace_id).one_or_none()
    finally:
        session.close()


def get_membership(workspace_id: int, user_id: int) -> Optional[WorkspaceMember]:
    session = new_session()
    try:
        return (
            session.query(WorkspaceMember)
            .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
            .one_or_none()
        )
    finally:
        session.close()


def list_members(workspace_id: int) -> list[tuple[WorkspaceMember, User]]:
    session = new_session()
    try:
        return (
            session.query(WorkspaceMember, User)
            .join(User, User.id == WorkspaceMember.user_id)
            .filter(WorkspaceMember.workspace_id == workspace_id)
            .order_by(WorkspaceMember.role.desc(), User.email.asc())
            .all()
        )
    finally:
        session.close()


def upsert_member(workspace_id: int, user_id: int, role: str) -> WorkspaceMember:
    session = new_session()
    try:
        member = (
            session.query(WorkspaceMember)
            .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
            .one_or_none()
        )
        if member is None:
            member = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)
            session.add(member)
        else:
            member.role = role
        session.commit()
        session.refresh(member)
        return member
    finally:
        session.close()


def delete_member(workspace_id: int, user_id: int) -> bool:
    session = new_session()
    try:
        member = (
            session.query(WorkspaceMember)
            .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
            .one_or_none()
        )
        if member is None:
            return False
        session.delete(member)
        session.commit()
        return True
    finally:
        session.close()


def owner_count(workspace_id: int) -> int:
    session = new_session()
    try:
        return (
            session.query(func.count(WorkspaceMember.id))
            .filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.role == "owner")
            .scalar()
            or 0
        )
    finally:
        session.close()


def role_at_least(role: str, minimum_role: str) -> bool:
    return ROLE_ORDER.get(role, 0) >= ROLE_ORDER[minimum_role]


def unique_slug(session: Session, name: str) -> str:
    base_slug = slugify(name) or "workspace"
    slug = base_slug
    suffix = 2
    while session.query(Workspace).filter(Workspace.slug == slug).one_or_none() is not None:
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
