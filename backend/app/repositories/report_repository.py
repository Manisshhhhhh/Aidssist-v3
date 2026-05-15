from __future__ import annotations

from pathlib import Path

from app.db.models import ReportRecord
from app.db.session import new_session
from app.models.report_models import ReportResponse


def create_report_record(response: ReportResponse, report_path: Path, json_path: Path) -> ReportRecord:
    session = new_session()
    try:
        existing = (
            session.query(ReportRecord)
            .filter(ReportRecord.dataset_id == response.dataset_id, ReportRecord.report_id == response.report_id)
            .one_or_none()
        )
        record = existing or ReportRecord(
            dataset_id=response.dataset_id,
            report_id=response.report_id,
            created_at=response.created_at,
            format=response.format,
            filename=response.filename,
            report_path=str(report_path),
            json_path=str(json_path),
        )
        record.format = response.format
        record.filename = response.filename
        record.report_path = str(report_path)
        record.json_path = str(json_path)
        if existing is None:
            session.add(record)
        session.commit()
        session.refresh(record)
        return record
    finally:
        session.close()


def get_report_record(dataset_id: str, report_id: str) -> ReportRecord | None:
    session = new_session()
    try:
        return (
            session.query(ReportRecord)
            .filter(ReportRecord.dataset_id == dataset_id, ReportRecord.report_id == report_id)
            .one_or_none()
        )
    finally:
        session.close()
