from __future__ import annotations

import json
import logging as py_logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.core.request_context import (
    get_dataset_id,
    get_job_id,
    get_request_id,
    get_user_id,
    get_workspace_id,
)


SENSITIVE_WORDS = ("password", "token", "authorization", "api_key", "secret", "jwt", "key")


class RequestContextFilter(py_logging.Filter):
    def filter(self, record: py_logging.LogRecord) -> bool:
        record.request_id = getattr(record, "request_id", None) or get_request_id()
        record.user_id = getattr(record, "user_id", None) or get_user_id()
        record.workspace_id = getattr(record, "workspace_id", None) or get_workspace_id()
        record.dataset_id = getattr(record, "dataset_id", None) or get_dataset_id()
        record.job_id = getattr(record, "job_id", None) or get_job_id()
        return True


class JsonFormatter(py_logging.Formatter):
    def format(self, record: py_logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "user_id": getattr(record, "user_id", None),
            "workspace_id": getattr(record, "workspace_id", None),
            "dataset_id": getattr(record, "dataset_id", None),
            "job_id": getattr(record, "job_id", None),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in payload or key in RESERVED_RECORD_KEYS:
                continue
            if any(word in key.lower() for word in SENSITIVE_WORDS):
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


RESERVED_RECORD_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(py_logging, settings.log_level.upper(), py_logging.INFO)
    handler = py_logging.StreamHandler()
    handler.addFilter(RequestContextFilter())
    if settings.log_format.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            py_logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s [request_id=%(request_id)s] %(message)s"
            )
        )

    root = py_logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> py_logging.Logger:
    return py_logging.getLogger(name)
