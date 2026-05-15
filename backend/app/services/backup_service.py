from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Any
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import func

from app.core.config import get_settings
from app.db.models import ArtifactRecord, DatasetRecord, JobRecord, ReportRecord
from app.db.session import new_session
from app.models.backup_models import BackupRequest, BackupResponse
from app.services import storage_service


EXCLUDED_DIRS = {".venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "backups"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


class BackupError(Exception):
    """Raised when a backup cannot be created or read safely."""


def backup_root() -> Path:
    root = Path(get_settings().backup_dir).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_backup(request: BackupRequest | None = None) -> BackupResponse:
    request = request or BackupRequest()
    root = backup_root()
    now = datetime.now(timezone.utc)
    backup_id = now.strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
    filename = f"aidssist_backup_{backup_id}.zip"
    path = root / filename

    manifest = build_manifest(now)
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        db_path = sqlite_db_path()
        if db_path and db_path.is_file():
            archive.write(db_path, "database/aidssist.db")
        if request.include_storage:
            add_directory(archive, storage_service.get_datasets_dir(), "datasets")
        if request.include_reports:
            add_directory(archive, Path(get_settings().reports_local_root).expanduser(), "reports")

    enforce_retention(root)
    return backup_response(path)


def list_backups() -> list[BackupResponse]:
    return [backup_response(path) for path in sorted(backup_root().glob("aidssist_backup_*.zip"), reverse=True)]


def get_backup_path(backup_id: str) -> Path:
    safe_id = safe_backup_id(backup_id)
    candidates = sorted(backup_root().glob(f"aidssist_backup_{safe_id}.zip"))
    if not candidates:
        raise BackupError("Backup was not found.")
    path = candidates[0].resolve()
    if not is_relative_to(path, backup_root().resolve()):
        raise BackupError("Backup was not found.")
    return path


def backup_response(path: Path) -> BackupResponse:
    stat = path.stat()
    backup_id = path.stem.replace("aidssist_backup_", "", 1)
    return BackupResponse(
        backup_id=backup_id,
        filename=path.name,
        size_bytes=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc),
    )


def build_manifest(created_at: datetime) -> dict[str, Any]:
    settings = get_settings()
    session = new_session()
    try:
        return {
            "created_at": created_at.isoformat(),
            "app_version": settings.app_version,
            "database_type": settings.database_url.split(":", 1)[0],
            "storage_backend": settings.storage_backend,
            "counts": {
                "artifacts": session.query(func.count(ArtifactRecord.id)).scalar() or 0,
                "datasets": session.query(func.count(DatasetRecord.id)).scalar() or 0,
                "reports": session.query(func.count(ReportRecord.id)).scalar() or 0,
                "jobs": session.query(func.count(JobRecord.id)).scalar() or 0,
            },
        }
    finally:
        session.close()


def add_directory(archive: ZipFile, source: Path, archive_prefix: str) -> None:
    source = source.expanduser()
    if not source.exists():
        return
    source = source.resolve()
    for path in sorted(item for item in source.rglob("*") if item.is_file()):
        if should_exclude(path):
            continue
        relative = path.relative_to(source).as_posix()
        archive.write(path, f"{archive_prefix}/{relative}")


def should_exclude(path: Path) -> bool:
    if path.name.startswith(".env") or path.suffix in EXCLUDED_SUFFIXES:
        return True
    if path.suffix == ".zip" and path.name.startswith("aidssist_backup_"):
        return True
    return any(part in EXCLUDED_DIRS for part in path.parts)


def sqlite_db_path() -> Path | None:
    database_url = get_settings().database_url
    if not database_url.startswith("sqlite:///"):
        return None
    raw_path = database_url.replace("sqlite:///", "", 1)
    if raw_path.startswith("/"):
        return Path(raw_path)
    return Path(raw_path).expanduser().resolve()


def enforce_retention(root: Path) -> None:
    settings = get_settings()
    backups = sorted(root.glob("aidssist_backup_*.zip"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in backups[settings.max_backup_count :]:
        path.unlink(missing_ok=True)
    if settings.backup_retention_days <= 0:
        return
    cutoff = datetime.now(timezone.utc).timestamp() - settings.backup_retention_days * 86400
    for path in backups:
        if path.exists() and path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)


def safe_backup_id(backup_id: str) -> str:
    if not backup_id or any(ch not in "0123456789_abcdefABCDEF-" for ch in backup_id):
        raise BackupError("Backup was not found.")
    return backup_id


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def copy_path(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
