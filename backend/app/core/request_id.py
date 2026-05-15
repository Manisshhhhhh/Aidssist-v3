from __future__ import annotations

import re
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.request_context import reset_request_id, set_request_id


SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
logger = get_logger(__name__)


def safe_request_id(value: str | None) -> str:
    if value and SAFE_REQUEST_ID.fullmatch(value):
        return value
    return str(uuid4())


async def add_request_context(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = safe_request_id(request.headers.get("X-Request-ID"))
    token = set_request_id(request_id)
    started = time.perf_counter()
    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    except Exception:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.exception(
            "request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else None,
            },
        )
        raise
    finally:
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        if response is not None:
            response.headers["X-Request-ID"] = request_id
            if get_settings().request_logging_enabled:
                logger.info(
                    "request completed",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "client_ip": request.client.host if request.client else None,
                    },
                )
        reset_request_id(token)
