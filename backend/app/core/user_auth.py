from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import TokenError, decode_access_token
from app.core.config import get_settings
from app.db.models import User
from app.repositories.user_repository import get_user_by_id


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[User]:
    settings = get_settings()
    if not settings.user_auth_enabled:
        return None

    if credentials is None or credentials.scheme.lower() != "bearer":
        return None

    return _user_from_token(credentials.credentials)


def get_current_user_required(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[User]:
    settings = get_settings()
    if not settings.user_auth_enabled:
        return None

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()

    return _user_from_token(credentials.credentials)


def _user_from_token(token: str) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (TokenError, ValueError) as exc:
        raise unauthorized() from exc

    user = get_user_by_id(user_id)
    if user is None:
        raise unauthorized()
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This user account is inactive.")
    return user


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
