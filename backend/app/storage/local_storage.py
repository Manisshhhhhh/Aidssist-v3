from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Optional

from app.storage.base import StoredObject, StorageKeyError, normalize_key


class LocalStorageProvider:
    backend = "local"

    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, key: str, data: bytes, content_type: Optional[str] = None) -> StoredObject:
        path = self._path_for_key(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return self._stored_object(normalize_key(key), path, content_type)

    def save_text(self, key: str, text: str, content_type: Optional[str] = None) -> StoredObject:
        return self.save_bytes(key, text.encode("utf-8"), content_type or "text/plain; charset=utf-8")

    def read_bytes(self, key: str) -> bytes:
        return self._path_for_key(key).read_bytes()

    def read_text(self, key: str) -> str:
        return self._path_for_key(key).read_text(encoding="utf-8")

    def exists(self, key: str) -> bool:
        return self._path_for_key(key).is_file()

    def delete(self, key: str) -> None:
        path = self._path_for_key(key)
        if path.is_file():
            path.unlink()

    def list(self, prefix: str) -> list[StoredObject]:
        safe_prefix = normalize_key(prefix) if prefix else ""
        start = self._path_for_key(safe_prefix) if safe_prefix else self.root
        if start.is_file():
            return [self._stored_object(safe_prefix, start, None)]
        if not start.exists():
            return []
        objects: list[StoredObject] = []
        for path in sorted(item for item in start.rglob("*") if item.is_file()):
            objects.append(self._stored_object(path.relative_to(self.root).as_posix(), path, None))
        return objects

    def get_local_path(self, key: str) -> Optional[Path]:
        return self._path_for_key(key)

    def _path_for_key(self, key: str) -> Path:
        safe_key = normalize_key(key)
        path = (self.root / safe_key).resolve()
        if not is_relative_to(path, self.root):
            raise StorageKeyError("Storage key resolves outside the storage root.")
        return path

    def _stored_object(self, key: str, path: Path, content_type: Optional[str]) -> StoredObject:
        data = path.read_bytes()
        return StoredObject(
            key=key,
            size_bytes=path.stat().st_size,
            content_type=content_type,
            checksum=sha256(data).hexdigest(),
            etag=sha256(data).hexdigest(),
            created_at=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc),
            backend=self.backend,
        )


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
