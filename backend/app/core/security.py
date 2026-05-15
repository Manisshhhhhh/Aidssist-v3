from __future__ import annotations

import hmac
from typing import Optional

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


API_KEY_HEADER = "X-Aidssist-API-Key"


def require_api_key(x_aidssist_api_key: Optional[str] = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.auth_enabled:
        return

    configured_key = settings.api_key
    if not configured_key or not x_aidssist_api_key:
        raise unauthorized()

    if not hmac.compare_digest(x_aidssist_api_key, configured_key):
        raise unauthorized()


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="This Aidssist server requires an API key.",
        headers={"WWW-Authenticate": API_KEY_HEADER},
    )
