from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.dataset_models import DatasetMetadata
from app.db.models import DatasetRecord
from app.db.session import new_session
from app.repositories.workspace_repository import get_or_create_default_workspace


def upsert_dataset(
    metadata: DatasetMetadata,
    storage_path: Path,
    metadata_path: Path,
    owner_user_id: int | None = None,
    workspace_id: int | None = None,
) -> DatasetRecord:
    session = new_session()
    try:
        workspace = get_or_create_default_workspace(session)
        target_workspace_id = workspace_id or workspace.id
        record = session.query(DatasetRecord).filter(DatasetRecord.dataset_id == metadata.dataset_id).one_or_none()
        if record is None:
            record = DatasetRecord(
                dataset_id=metadata.dataset_id,
                workspace_id=target_workspace_id,
                owner_user_id=owner_user_id,
                created_at=metadata.created_at,
                original_filename=metadata.original_filename,
                stored_filename=metadata.stored_filename,
                file_size_bytes=metadata.file_size_bytes,
                content_type=metadata.content_type,
                row_count=metadata.row_count,
                column_count=metadata.column_count,
                columns_json=json.dumps(metadata.columns or []),
                storage_path=str(storage_path),
                metadata_path=str(metadata_path),
            )
            session.add(record)
        else:
            record.workspace_id = target_workspace_id
            record.owner_user_id = owner_user_id
            record.original_filename = metadata.original_filename
            record.stored_filename = metadata.stored_filename
            record.file_size_bytes = metadata.file_size_bytes
            record.content_type = metadata.content_type
            record.row_count = metadata.row_count
            record.column_count = metadata.column_count
            record.columns_json = json.dumps(metadata.columns or [])
            record.storage_path = str(storage_path)
            record.metadata_path = str(metadata_path)
            record.created_at = metadata.created_at

        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def list_dataset_records(
    owner_user_id: int | None = None,
    include_ownerless: bool = True,
    workspace_id: int | None = None,
    workspace_ids: list[int] | None = None,
) -> list[DatasetRecord]:
    session = new_session()
    try:
        query = session.query(DatasetRecord)
        if owner_user_id is not None:
            query = query.filter(DatasetRecord.owner_user_id == owner_user_id)
        elif not include_ownerless:
            query = query.filter(DatasetRecord.owner_user_id.isnot(None))
        if workspace_id is not None:
            query = query.filter(DatasetRecord.workspace_id == workspace_id)
        if workspace_ids is not None:
            if not workspace_ids:
                return []
            query = query.filter(DatasetRecord.workspace_id.in_(workspace_ids))
        return query.order_by(DatasetRecord.created_at.desc(), DatasetRecord.id.desc()).all()
    finally:
        session.close()


def get_dataset_record(dataset_id: str) -> DatasetRecord | None:
    session = new_session()
    try:
        return session.query(DatasetRecord).filter(DatasetRecord.dataset_id == dataset_id).one_or_none()
    finally:
        session.close()


def delete_dataset_record(dataset_id: str) -> bool:
    session = new_session()
    try:
        record = session.query(DatasetRecord).filter(DatasetRecord.dataset_id == dataset_id).one_or_none()
        if record is None:
            return False
        session.delete(record)
        session.commit()
        return True
    finally:
        session.close()


def metadata_from_record(record: DatasetRecord) -> DatasetMetadata:
    columns = json.loads(record.columns_json) if record.columns_json else []
    return DatasetMetadata(
        dataset_id=record.dataset_id,
        workspace_id=record.workspace_id,
        original_filename=record.original_filename,
        stored_filename=record.stored_filename,
        file_size_bytes=record.file_size_bytes,
        content_type=record.content_type,
        created_at=record.created_at,
        row_count=record.row_count,
        column_count=record.column_count,
        columns=columns,
    )


def upsert_dataset_with_session(
    session: Session,
    metadata: DatasetMetadata,
    storage_path: Path,
    metadata_path: Path,
    owner_user_id: int | None = None,
    workspace_id: int | None = None,
) -> DatasetRecord:
    workspace = get_or_create_default_workspace(session)
    target_workspace_id = workspace_id or workspace.id
    record = session.query(DatasetRecord).filter(DatasetRecord.dataset_id == metadata.dataset_id).one_or_none()
    if record is None:
        record = DatasetRecord(
            dataset_id=metadata.dataset_id,
            workspace_id=target_workspace_id,
            owner_user_id=owner_user_id,
            created_at=metadata.created_at,
            original_filename=metadata.original_filename,
            stored_filename=metadata.stored_filename,
            file_size_bytes=metadata.file_size_bytes,
            content_type=metadata.content_type,
            row_count=metadata.row_count,
            column_count=metadata.column_count,
            columns_json=json.dumps(metadata.columns or []),
            storage_path=str(storage_path),
            metadata_path=str(metadata_path),
        )
        session.add(record)
    else:
        record.workspace_id = target_workspace_id
        record.owner_user_id = owner_user_id
        record.original_filename = metadata.original_filename
        record.stored_filename = metadata.stored_filename
        record.file_size_bytes = metadata.file_size_bytes
        record.content_type = metadata.content_type
        record.row_count = metadata.row_count
        record.column_count = metadata.column_count
        record.columns_json = json.dumps(metadata.columns or [])
        record.storage_path = str(storage_path)
        record.metadata_path = str(metadata_path)
        record.created_at = metadata.created_at
    return record
