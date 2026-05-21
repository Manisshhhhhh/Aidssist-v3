from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DatasetMetadata(BaseModel):
    dataset_id: str
    workspace_id: Optional[int] = None
    original_filename: str
    stored_filename: str
    file_size_bytes: int
    content_type: Optional[str] = None
    created_at: datetime
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    columns: Optional[list[str]] = None
    last_analyzed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DatasetListResponse(BaseModel):
    datasets: list[DatasetMetadata]


class DatasetDeleteResponse(BaseModel):
    dataset_id: str
    deleted: bool
    message: str


class DatasetUpdateRequest(BaseModel):
    original_filename: str = Field(min_length=1, max_length=512)
