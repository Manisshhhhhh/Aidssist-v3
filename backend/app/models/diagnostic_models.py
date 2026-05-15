from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobDiagnosticCounts(BaseModel):
    queued: int
    running: int
    failed: int


class DiagnosticCounts(BaseModel):
    workspaces: int
    datasets: int
    artifacts: int
    jobs: JobDiagnosticCounts


class SystemDiagnosticsResponse(BaseModel):
    app_version: str
    environment: str
    database_type: str
    storage_backend: str
    async_jobs_enabled: bool
    user_auth_enabled: bool
    api_key_auth_enabled: bool
    rate_limit_enabled: bool
    audit_log_enabled: bool
    request_logging_enabled: bool
    llm_enabled: bool
    llm_provider: str
    llm_model: str
    llm_key_configured: bool
    counts: DiagnosticCounts
    created_at: datetime


class RecentFailedJob(BaseModel):
    job_id: str
    job_type: str
    dataset_id: Optional[str]
    error_message: Optional[str]
    finished_at: Optional[datetime]


class RecentErrorDiagnosticsResponse(BaseModel):
    failed_jobs: list[RecentFailedJob]
    failed_audit_event_count: int
    created_at: datetime
