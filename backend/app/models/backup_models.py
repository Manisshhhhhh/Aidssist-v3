from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BackupRequest(BaseModel):
    include_storage: bool = True
    include_reports: bool = True


class BackupResponse(BaseModel):
    backup_id: str
    filename: str
    size_bytes: int
    created_at: datetime


class BackupListResponse(BaseModel):
    backups: list[BackupResponse]
