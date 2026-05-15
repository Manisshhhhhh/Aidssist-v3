from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings


READ_ONLY_DETAIL = "Aidssist is in read-only maintenance mode."
SAFE_MODE_DETAIL = "Aidssist is in emergency safe mode."


async def enforce_maintenance_mode(request: Request, call_next):
    settings = get_settings()
    if not (settings.safe_mode or settings.read_only_mode):
        return await call_next(request)

    if is_allowed_during_maintenance(request):
        return await call_next(request)

    return JSONResponse(
        status_code=423 if settings.read_only_mode else 503,
        content={"detail": SAFE_MODE_DETAIL if settings.safe_mode else READ_ONLY_DETAIL},
    )


def is_allowed_during_maintenance(request: Request) -> bool:
    method = request.method.upper()
    path = request.url.path

    if method in {"GET", "HEAD", "OPTIONS"}:
        return is_allowed_read_path(path)

    if method == "POST" and path in {"/auth/login"}:
        return True

    return False


def is_allowed_read_path(path: str) -> bool:
    allowed_exact = {"/", "/health", "/auth/status", "/auth/me", "/diagnostics/system", "/diagnostics/errors/recent", "/diagnostics/preflight"}
    if path in allowed_exact:
        return True
    allowed_prefixes = (
        "/datasets",
        "/artifacts",
        "/jobs",
        "/audit/events",
        "/backups",
        "/docs",
        "/openapi.json",
        "/redoc",
    )
    return any(path.startswith(prefix) for prefix in allowed_prefixes)
