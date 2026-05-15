from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from app.db.models import ArtifactRecord
from app.db.session import new_session
from app.models.artifact_models import ArtifactResponse, ArtifactType


def upsert_artifact(
    artifact_type: ArtifactType,
    storage_backend: str,
    storage_key: str,
    filename: str,
    size_bytes: int,
    content_type: Optional[str] = None,
    checksum: Optional[str] = None,
    dataset_id: Optional[str] = None,
    workspace_id: Optional[int] = None,
    created_by_user_id: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> ArtifactRecord:
    session = new_session()
    try:
        record = (
            session.query(ArtifactRecord)
            .filter(
                ArtifactRecord.storage_key == storage_key,
                ArtifactRecord.artifact_type == artifact_type,
                ArtifactRecord.deleted_at.is_(None),
            )
            .one_or_none()
        )
        now = datetime.now(timezone.utc)
        if record is None:
            record = ArtifactRecord(
                artifact_id=str(uuid4()),
                artifact_type=artifact_type,
                storage_backend=storage_backend,
                storage_key=storage_key,
                filename=filename,
                size_bytes=size_bytes,
                content_type=content_type,
                checksum=checksum,
                dataset_id=dataset_id,
                workspace_id=workspace_id,
                created_by_user_id=created_by_user_id,
                metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
                created_at=now,
                updated_at=now,
            )
            session.add(record)
        else:
            record.storage_backend = storage_backend
            record.filename = filename
            record.size_bytes = size_bytes
            record.content_type = content_type
            record.checksum = checksum
            record.dataset_id = dataset_id
            record.workspace_id = workspace_id
            record.created_by_user_id = created_by_user_id
            record.metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
            record.updated_at = now
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def get_artifact(artifact_id: str) -> Optional[ArtifactRecord]:
    session = new_session()
    try:
        return (
            session.query(ArtifactRecord)
            .filter(ArtifactRecord.artifact_id == artifact_id, ArtifactRecord.deleted_at.is_(None))
            .one_or_none()
        )
    finally:
        session.close()


def list_dataset_artifacts(dataset_id: str, include_deleted: bool = False) -> list[ArtifactRecord]:
    session = new_session()
    try:
        query = session.query(ArtifactRecord).filter(ArtifactRecord.dataset_id == dataset_id)
        if not include_deleted:
            query = query.filter(ArtifactRecord.deleted_at.is_(None))
        return query.order_by(ArtifactRecord.created_at.desc(), ArtifactRecord.id.desc()).all()
    finally:
        session.close()


def latest_dataset_artifact(dataset_id: str, artifact_type: ArtifactType) -> Optional[ArtifactRecord]:
    session = new_session()
    try:
        return (
            session.query(ArtifactRecord)
            .filter(
                ArtifactRecord.dataset_id == dataset_id,
                ArtifactRecord.artifact_type == artifact_type,
                ArtifactRecord.deleted_at.is_(None),
            )
            .order_by(ArtifactRecord.created_at.desc(), ArtifactRecord.id.desc())
            .first()
        )
    finally:
        session.close()


def soft_delete_artifact(artifact_id: str) -> bool:
    session = new_session()
    try:
        record = session.query(ArtifactRecord).filter(ArtifactRecord.artifact_id == artifact_id).one_or_none()
        if record is None or record.deleted_at is not None:
            return False
        record.deleted_at = datetime.now(timezone.utc)
        record.updated_at = record.deleted_at
        session.commit()
        return True
    finally:
        session.close()


def list_active_artifacts(limit: int = 10000) -> list[ArtifactRecord]:
    session = new_session()
    try:
        return (
            session.query(ArtifactRecord)
            .filter(ArtifactRecord.deleted_at.is_(None))
            .order_by(ArtifactRecord.created_at.desc(), ArtifactRecord.id.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()


def list_soft_deleted_artifacts(limit: int = 10000) -> list[ArtifactRecord]:
    session = new_session()
    try:
        return (
            session.query(ArtifactRecord)
            .filter(ArtifactRecord.deleted_at.isnot(None))
            .order_by(ArtifactRecord.deleted_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        session.close()


def artifact_to_response(record: ArtifactRecord) -> ArtifactResponse:
    return ArtifactResponse(
        artifact_id=record.artifact_id,
        workspace_id=record.workspace_id,
        dataset_id=record.dataset_id,
        artifact_type=record.artifact_type,
        filename=record.filename,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        checksum=record.checksum,
        storage_backend=record.storage_backend,
        created_at=record.created_at,
        updated_at=record.updated_at,
        deleted_at=record.deleted_at,
        download_url=f"/artifacts/{record.artifact_id}/download" if record.deleted_at is None else None,
    )
