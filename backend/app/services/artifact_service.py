from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from app.db.models import ArtifactRecord, User
from app.models.artifact_models import ArtifactResponse, ArtifactType
from app.repositories import artifact_repository
from app.repositories.dataset_repository import get_dataset_record
from app.services import storage_service
from app.services.workspace_service import can_access_workspace
from app.storage.base import StoredObject


class ArtifactNotFoundError(Exception):
    """Raised when an artifact does not exist or is unavailable."""


class ArtifactPermissionError(Exception):
    """Raised when a user cannot access an artifact."""


def record_artifact(
    artifact_type: ArtifactType,
    stored: StoredObject,
    filename: str,
    dataset_id: Optional[str] = None,
    workspace_id: Optional[int] = None,
    created_by_user_id: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> ArtifactRecord:
    if workspace_id is None and dataset_id:
        dataset_record = get_dataset_record(dataset_id)
        if dataset_record is not None:
            workspace_id = dataset_record.workspace_id
            if created_by_user_id is None:
                created_by_user_id = dataset_record.owner_user_id
    return artifact_repository.upsert_artifact(
        artifact_type=artifact_type,
        storage_backend=stored.backend,
        storage_key=stored.key,
        filename=filename,
        size_bytes=stored.size_bytes,
        content_type=stored.content_type,
        checksum=stored.checksum or stored.etag,
        dataset_id=dataset_id,
        workspace_id=workspace_id,
        created_by_user_id=created_by_user_id,
        metadata=metadata,
    )


def record_path_artifact(
    artifact_type: ArtifactType,
    storage_key: str,
    filename: str,
    dataset_id: Optional[str] = None,
    workspace_id: Optional[int] = None,
    created_by_user_id: Optional[int] = None,
    content_type: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> ArtifactRecord:
    provider = storage_service.get_provider()
    local_path = provider.get_local_path(storage_key)
    if local_path is None or not local_path.is_file():
        raise ArtifactNotFoundError("Storage object does not exist.")
    stored = provider.save_bytes(storage_key, local_path.read_bytes(), content_type)
    return record_artifact(
        artifact_type=artifact_type,
        stored=stored,
        filename=filename,
        dataset_id=dataset_id,
        workspace_id=workspace_id,
        created_by_user_id=created_by_user_id,
        metadata=metadata,
    )


def list_dataset_artifacts(dataset_id: str) -> list[ArtifactResponse]:
    return [
        artifact_repository.artifact_to_response(record)
        for record in artifact_repository.list_dataset_artifacts(dataset_id)
    ]


def get_artifact_for_download(artifact_id: str, current_user: Optional[User]) -> tuple[ArtifactRecord, Optional[Path]]:
    record = artifact_repository.get_artifact(artifact_id)
    if record is None:
        raise ArtifactNotFoundError("Artifact was not found.")
    if not can_view_artifact(record, current_user):
        raise ArtifactNotFoundError("Artifact was not found.")
    provider = storage_service.get_provider()
    if not provider.exists(record.storage_key):
        raise ArtifactNotFoundError("Artifact storage object was not found.")
    return record, provider.get_local_path(record.storage_key)


def can_view_artifact(record: ArtifactRecord, current_user: Optional[User]) -> bool:
    if current_user is None:
        return True
    if current_user.is_admin:
        return True
    if record.created_by_user_id == current_user.id:
        return True
    if record.workspace_id is not None:
        return can_access_workspace(record.workspace_id, current_user, "viewer")
    return False


def soft_delete_artifact(artifact_id: str) -> bool:
    return artifact_repository.soft_delete_artifact(artifact_id)


def audit_artifacts() -> dict[str, Any]:
    provider = storage_service.get_provider()
    active = artifact_repository.list_active_artifacts()
    soft_deleted = artifact_repository.list_soft_deleted_artifacts()
    missing = [record for record in active if not provider.exists(record.storage_key)]
    known_keys = {record.storage_key for record in active}
    storage_objects = provider.list("")
    orphans = [stored for stored in storage_objects if stored.key not in known_keys]
    return {
        "total_artifacts": len(active),
        "missing_storage_objects": missing,
        "orphan_storage_objects": orphans,
        "soft_deleted_artifacts": len(soft_deleted),
    }
