from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Optional


_request_id: ContextVar[Optional[str]] = ContextVar("aidssist_request_id", default=None)
_user_id: ContextVar[Optional[int]] = ContextVar("aidssist_user_id", default=None)
_workspace_id: ContextVar[Optional[int]] = ContextVar("aidssist_workspace_id", default=None)
_dataset_id: ContextVar[Optional[str]] = ContextVar("aidssist_dataset_id", default=None)
_job_id: ContextVar[Optional[str]] = ContextVar("aidssist_job_id", default=None)


def set_request_id(value: str) -> Token[Optional[str]]:
    return _request_id.set(value)


def reset_request_id(token: Token[Optional[str]]) -> None:
    _request_id.reset(token)


def get_request_id() -> Optional[str]:
    return _request_id.get()


def set_user_id(value: Optional[int]) -> Token[Optional[int]]:
    return _user_id.set(value)


def reset_user_id(token: Token[Optional[int]]) -> None:
    _user_id.reset(token)


def get_user_id() -> Optional[int]:
    return _user_id.get()


def set_workspace_id(value: Optional[int]) -> Token[Optional[int]]:
    return _workspace_id.set(value)


def reset_workspace_id(token: Token[Optional[int]]) -> None:
    _workspace_id.reset(token)


def get_workspace_id() -> Optional[int]:
    return _workspace_id.get()


def set_dataset_id(value: Optional[str]) -> Token[Optional[str]]:
    return _dataset_id.set(value)


def reset_dataset_id(token: Token[Optional[str]]) -> None:
    _dataset_id.reset(token)


def get_dataset_id() -> Optional[str]:
    return _dataset_id.get()


def set_job_id(value: Optional[str]) -> Token[Optional[str]]:
    return _job_id.set(value)


def reset_job_id(token: Token[Optional[str]]) -> None:
    _job_id.reset(token)


def get_job_id() -> Optional[str]:
    return _job_id.get()
