from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
from typing import Optional

import pandas as pd
from fastapi import UploadFile
from pandas.errors import ParserError

from app.core.config import get_settings
from app.models.dataset_models import DatasetMetadata
from app.repositories import dataset_repository
from app.services import artifact_service
from app.services import storage_service


class DatasetValidationError(Exception):
    """Raised when an uploaded dataset cannot be accepted."""


SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}


def sanitize_filename(filename: Optional[str]) -> str:
    if not filename:
        return "uploaded.csv"

    safe_name = Path(filename).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", safe_name).strip("._")
    return safe_name or "uploaded.csv"


def validate_dataset_filename(filename: Optional[str]) -> str:
    safe_name = sanitize_filename(filename)
    if Path(safe_name).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise DatasetValidationError("Only CSV and Excel .xlsx files are supported.")
    return safe_name


def generate_dataset_id(content: bytes, owner_user_id: Optional[int] = None) -> str:
    digest = sha256(content)
    if owner_user_id is not None:
        digest.update(f":owner:{owner_user_id}".encode("utf-8"))
    return digest.hexdigest()[:16]


def parse_uploaded_dataframe(content: bytes, original_filename: str) -> pd.DataFrame:
    suffix = Path(original_filename).suffix.lower()

    try:
        if suffix == ".csv":
            return pd.read_csv(BytesIO(content))
        if suffix == ".xlsx":
            return pd.read_excel(BytesIO(content), engine="openpyxl")
    except (ParserError, UnicodeDecodeError, ValueError, ImportError) as exc:
        raise DatasetValidationError("Uploaded file is not a valid readable dataset.") from exc

    raise DatasetValidationError("Only CSV and Excel .xlsx files are supported.")


def extract_basic_metadata(dataframe: pd.DataFrame) -> tuple[int, int, list[str]]:

    if dataframe.columns.empty:
        raise DatasetValidationError("CSV must contain at least one column.")

    columns = [str(column) for column in dataframe.columns.tolist()]
    if dataframe.shape[0] == 0:
        raise DatasetValidationError("CSV must contain at least one data row.")

    return int(dataframe.shape[0]), int(dataframe.shape[1]), columns


async def create_dataset_from_upload(
    file: Optional[UploadFile],
    owner_user_id: Optional[int] = None,
    workspace_id: Optional[int] = None,
) -> DatasetMetadata:
    if file is None:
        raise DatasetValidationError("A CSV or Excel .xlsx file is required.")

    original_filename = validate_dataset_filename(file.filename)
    content = await file.read()
    max_bytes = get_settings().max_upload_size_mb * 1024 * 1024

    if not content:
        raise DatasetValidationError("Uploaded dataset file is empty.")

    if len(content) > max_bytes:
        raise DatasetValidationError(
            f"Dataset files must be {get_settings().max_upload_size_mb}MB or smaller."
        )

    dataframe = parse_uploaded_dataframe(content, original_filename)
    row_count, column_count, columns = extract_basic_metadata(dataframe)
    dataset_id = generate_dataset_id(content, owner_user_id=owner_user_id)
    canonical_csv = dataframe.to_csv(index=False).encode("utf-8")

    metadata = DatasetMetadata(
        dataset_id=dataset_id,
        workspace_id=workspace_id,
        original_filename=original_filename,
        stored_filename=storage_service.ORIGINAL_FILENAME,
        file_size_bytes=len(content),
        content_type=file.content_type,
        created_at=datetime.now(timezone.utc),
        row_count=row_count,
        column_count=column_count,
        columns=columns,
    )

    original_path = storage_service.save_original_file(dataset_id, canonical_csv)
    metadata_path = storage_service.save_metadata(metadata)
    dataset_repository.upsert_dataset(
        metadata,
        storage_path=original_path,
        metadata_path=metadata_path,
        owner_user_id=owner_user_id,
        workspace_id=workspace_id,
    )
    artifact_service.record_path_artifact(
        artifact_type="original_csv",
        storage_key=storage_service.get_original_key(dataset_id),
        filename=storage_service.ORIGINAL_FILENAME,
        dataset_id=dataset_id,
        workspace_id=workspace_id,
        created_by_user_id=owner_user_id,
        content_type="text/csv",
        metadata={"original_filename": original_filename},
    )
    artifact_service.record_path_artifact(
        artifact_type="metadata_json",
        storage_key=storage_service.get_metadata_key(dataset_id),
        filename=storage_service.METADATA_FILENAME,
        dataset_id=dataset_id,
        workspace_id=workspace_id,
        created_by_user_id=owner_user_id,
        content_type="application/json",
    )
    return metadata


def list_datasets(
    owner_user_id: Optional[int] = None,
    include_ownerless: bool = True,
    workspace_id: Optional[int] = None,
    workspace_ids: Optional[list[int]] = None,
) -> list[DatasetMetadata]:
    records = dataset_repository.list_dataset_records(
        owner_user_id=owner_user_id,
        include_ownerless=include_ownerless,
        workspace_id=workspace_id,
        workspace_ids=workspace_ids,
    )
    if records:
        return [dataset_repository.metadata_from_record(record) for record in records]
    return storage_service.list_metadata()


def get_dataset(dataset_id: str) -> Optional[DatasetMetadata]:
    record = dataset_repository.get_dataset_record(dataset_id)
    if record is not None:
        return dataset_repository.metadata_from_record(record)
    return storage_service.load_metadata(dataset_id)


def delete_dataset(dataset_id: str) -> bool:
    deleted_files = storage_service.delete_dataset(dataset_id)
    deleted_record = dataset_repository.delete_dataset_record(dataset_id)
    return deleted_files or deleted_record
