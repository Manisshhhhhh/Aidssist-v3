from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


ArtifactType = Literal[
    "original_csv",
    "metadata_json",
    "analysis_json",
    "forecast_json",
    "report_html",
    "report_json",
    "ai_summary_json",
    "other",
]


class ArtifactResponse(BaseModel):
    artifact_id: str
    workspace_id: Optional[int] = None
    dataset_id: Optional[str] = None
    artifact_type: ArtifactType
    filename: str
    content_type: Optional[str] = None
    size_bytes: int
    checksum: Optional[str] = None
    storage_backend: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    download_url: Optional[str] = None


class DatasetArtifactsResponse(BaseModel):
    artifacts: list[ArtifactResponse]
