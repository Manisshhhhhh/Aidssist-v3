from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.storage.base import StoredObject, normalize_key


class S3StorageProvider:
    backend = "s3"

    def __init__(self, bucket: str, prefix: str = "aidssist") -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")

    def save_bytes(self, key: str, data: bytes, content_type: Optional[str] = None) -> StoredObject:
        normalize_key(key)
        raise NotImplementedError("S3 storage is scaffolded but not enabled in this local build.")

    def save_text(self, key: str, text: str, content_type: Optional[str] = None) -> StoredObject:
        return self.save_bytes(key, text.encode("utf-8"), content_type)

    def read_bytes(self, key: str) -> bytes:
        normalize_key(key)
        raise NotImplementedError("S3 storage is scaffolded but not enabled in this local build.")

    def read_text(self, key: str) -> str:
        return self.read_bytes(key).decode("utf-8")

    def exists(self, key: str) -> bool:
        normalize_key(key)
        raise NotImplementedError("S3 storage is scaffolded but not enabled in this local build.")

    def delete(self, key: str) -> None:
        normalize_key(key)
        raise NotImplementedError("S3 storage is scaffolded but not enabled in this local build.")

    def list(self, prefix: str) -> list[StoredObject]:
        normalize_key(prefix) if prefix else ""
        raise NotImplementedError("S3 storage is scaffolded but not enabled in this local build.")

    def get_local_path(self, key: str) -> Optional[Path]:
        normalize_key(key)
        return None
