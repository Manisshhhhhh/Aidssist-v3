from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
import time

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


_requests: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def rate_limited(request: Request) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return

    limit = max(1, settings.rate_limit_requests)
    window_seconds = max(1, settings.rate_limit_window_seconds)
    client_host = request.client.host if request.client else "unknown"
    key = f"{client_host}:{request.url.path}"
    now = time.monotonic()
    window_start = now - window_seconds

    with _lock:
        timestamps = _requests[key]
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before trying again.",
            )

        timestamps.append(now)


def clear_rate_limit_state() -> None:
    with _lock:
        _requests.clear()
