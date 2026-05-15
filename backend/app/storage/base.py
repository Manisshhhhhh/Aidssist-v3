from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol
import posixpath
import re


class StorageKeyError(ValueError):
    """Raised when a logical storage key is unsafe."""


@dataclass(frozen=True)
class StoredObject:
    key: str
    size_bytes: int
    content_type: Optional[str]
    etag: Optional[str] = None
    checksum: Optional[str] = None
    created_at: Optional[datetime] = None
    backend: str = "local"


class StorageProvider(Protocol):
    backend: str

    def save_bytes(self, key: str, data: bytes, content_type: Optional[str] = None) -> StoredObject:
        ...

    def save_text(self, key: str, text: str, content_type: Optional[str] = None) -> StoredObject:
        ...

    def read_bytes(self, key: str) -> bytes:
        ...

    def read_text(self, key: str) -> str:
        ...

    def exists(self, key: str) -> bool:
        ...

    def delete(self, key: str) -> None:
        ...

    def list(self, prefix: str) -> list[StoredObject]:
        ...

    def get_local_path(self, key: str) -> Optional[Path]:
        ...


def normalize_key(key: str) -> str:
    if not key or key.startswith("/") or "\\" in key:
        raise StorageKeyError("Storage key must be a relative POSIX path.")
    normalized = posixpath.normpath(key).strip("/")
    if normalized in {"", "."} or normalized.startswith("../") or "/../" in f"/{normalized}/":
        raise StorageKeyError("Storage key cannot traverse outside the storage root.")
    if re.search(r"(^|/)\.\.?($|/)", normalized):
        raise StorageKeyError("Storage key cannot contain dot path segments.")
    return normalized
