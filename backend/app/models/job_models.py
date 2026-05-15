from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


JobStatus = Literal["queued", "running", "succeeded", "failed", "cancelled"]
JobType = Literal["analysis", "forecast", "report", "filesystem_sync", "future_reserved"]


class JobCreateResponse(BaseModel):
    job_id: str
    job_type: JobType
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    status_url: str
    created_at: datetime


class JobResponse(BaseModel):
    job_id: str
    job_type: JobType
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    dataset_id: Optional[str] = None
    workspace_id: Optional[int] = None
    output: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    attempts: int
    max_attempts: int
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
