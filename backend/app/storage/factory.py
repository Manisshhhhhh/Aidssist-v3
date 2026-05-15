from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.storage.base import StorageProvider
from app.storage.local_storage import LocalStorageProvider
from app.storage.s3_storage import S3StorageProvider


class StorageConfigurationError(RuntimeError):
    """Raised when the configured storage backend cannot be initialized."""


def get_storage_provider(local_root: Optional[Path] = None) -> StorageProvider:
    settings = get_settings()
    backend = settings.storage_backend.lower()
    if backend == "local":
        return LocalStorageProvider(local_root or Path(settings.storage_local_root))
    if backend == "s3":
        if not settings.s3_bucket:
            raise StorageConfigurationError("AIDSSIST_S3_BUCKET is required when AIDSSIST_STORAGE_BACKEND=s3.")
        return S3StorageProvider(bucket=settings.s3_bucket, prefix=settings.s3_prefix)
    raise StorageConfigurationError(f"Unsupported storage backend '{settings.storage_backend}'.")
