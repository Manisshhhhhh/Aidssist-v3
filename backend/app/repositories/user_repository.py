from __future__ import annotations

from typing import Optional

from app.db.models import User
from app.db.session import new_session


def create_user(email: str, full_name: str, password_hash: str) -> User:
    session = new_session()
    try:
        user = User(email=email, full_name=full_name.strip(), password_hash=password_hash)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def get_user_by_email(email: str) -> Optional[User]:
    session = new_session()
    try:
        return session.query(User).filter(User.email == email).one_or_none()
    finally:
        session.close()


def get_user_by_id(user_id: int) -> Optional[User]:
    session = new_session()
    try:
        return session.query(User).filter(User.id == user_id).one_or_none()
    finally:
        session.close()


def set_user_admin(user_id: int, is_admin: bool = True) -> Optional[User]:
    session = new_session()
    try:
        user = session.query(User).filter(User.id == user_id).one_or_none()
        if user is None:
            return None
        user.is_admin = is_admin
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()
