from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
from typing import Optional

from app.core import paths
from app.models.analysis_models import AnalysisResult
from app.models.dataset_models import DatasetMetadata
from app.storage.factory import get_storage_provider


ORIGINAL_FILENAME = "original.csv"
METADATA_FILENAME = "metadata.json"
ANALYSIS_FILENAME = "analysis.json"


def get_datasets_dir() -> Path:
    return paths.DATASETS_DIR


def ensure_datasets_dir() -> Path:
    datasets_dir = get_datasets_dir()
    datasets_dir.mkdir(parents=True, exist_ok=True)
    return datasets_dir


def get_provider():
    return get_storage_provider(local_root=get_datasets_dir())


def dataset_key(dataset_id: str, filename: str) -> str:
    return f"{sanitize_dataset_id(dataset_id)}/{filename}"


def get_original_key(dataset_id: str) -> str:
    return dataset_key(dataset_id, ORIGINAL_FILENAME)


def get_metadata_key(dataset_id: str) -> str:
    return dataset_key(dataset_id, METADATA_FILENAME)


def get_analysis_key(dataset_id: str) -> str:
    return dataset_key(dataset_id, ANALYSIS_FILENAME)


def get_forecast_key(dataset_id: str, filename: str) -> str:
    return dataset_key(dataset_id, filename)


def get_report_key(dataset_id: str, report_id: str, filename: str) -> str:
    return dataset_key(dataset_id, f"reports/{report_id}/{filename}")


def get_dataset_dir(dataset_id: str) -> Path:
    return ensure_datasets_dir() / sanitize_dataset_id(dataset_id)


def dataset_exists(dataset_id: str) -> bool:
    return (get_dataset_dir(dataset_id) / METADATA_FILENAME).is_file()


def create_dataset_dir(dataset_id: str) -> Path:
    dataset_dir = get_dataset_dir(dataset_id)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    return dataset_dir


def save_original_file(dataset_id: str, content: bytes) -> Path:
    stored = get_provider().save_bytes(get_original_key(dataset_id), content, "text/csv")
    local_path = get_provider().get_local_path(stored.key)
    if local_path is None:
        raise RuntimeError("Local path is unavailable for original file.")
    return local_path


def get_original_file_path(dataset_id: str) -> Path:
    return get_dataset_dir(dataset_id) / ORIGINAL_FILENAME


def get_analysis_path(dataset_id: str) -> Path:
    return get_dataset_dir(dataset_id) / ANALYSIS_FILENAME


def save_metadata(metadata: DatasetMetadata) -> Path:
    stored = get_provider().save_text(
        get_metadata_key(metadata.dataset_id),
        metadata.model_dump_json(indent=2),
        "application/json",
    )
    local_path = get_provider().get_local_path(stored.key)
    if local_path is None:
        raise RuntimeError("Local path is unavailable for metadata file.")
    return local_path


def save_analysis(analysis: AnalysisResult) -> Path:
    stored = get_provider().save_text(
        get_analysis_key(analysis.dataset_id),
        analysis.model_dump_json(indent=2),
        "application/json",
    )
    local_path = get_provider().get_local_path(stored.key)
    if local_path is None:
        raise RuntimeError("Local path is unavailable for analysis file.")
    return local_path


def load_metadata(dataset_id: str) -> Optional[DatasetMetadata]:
    metadata_path = get_dataset_dir(dataset_id) / METADATA_FILENAME
    if not metadata_path.is_file():
        return None

    with metadata_path.open("r", encoding="utf-8") as metadata_file:
        payload = json.load(metadata_file)
    return DatasetMetadata.model_validate(payload)


def list_metadata() -> list[DatasetMetadata]:
    datasets_dir = ensure_datasets_dir()
    metadata_items: list[DatasetMetadata] = []

    for metadata_path in sorted(datasets_dir.glob(f"*/{METADATA_FILENAME}")):
        with metadata_path.open("r", encoding="utf-8") as metadata_file:
            payload = json.load(metadata_file)
        metadata_items.append(DatasetMetadata.model_validate(payload))

    return sorted(metadata_items, key=lambda item: item.created_at, reverse=True)


def delete_dataset(dataset_id: str) -> bool:
    dataset_dir = get_dataset_dir(dataset_id)
    metadata_path = dataset_dir / METADATA_FILENAME
    if not metadata_path.is_file():
        return False

    shutil.rmtree(dataset_dir)
    return True


def sanitize_dataset_id(dataset_id: str) -> str:
    safe_dataset_id = re.sub(r"[^A-Za-z0-9._-]+", "_", dataset_id).strip("._")
    return safe_dataset_id or "invalid_dataset"
