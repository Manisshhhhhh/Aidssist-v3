from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.core import paths
from app.db.init_db import DEFAULT_WORKSPACE_SLUG
from app.db.models import AnalysisRecord, DatasetRecord, ForecastRecord, ReportRecord, Workspace
from app.db.session import new_session
from app.models.dataset_models import DatasetMetadata
from app.repositories.dataset_repository import delete_dataset_record
from app.services import storage_service
from scripts.sync_filesystem_to_db import sync_filesystem_to_db


def upload_csv(client: TestClient, content: bytes | None = None) -> str:
    payload = content or b"date,region,sales,profit\n2026-01-01,North,10,1\n2026-01-02,South,20,2\n2026-01-03,North,30,3\n2026-01-04,South,40,4\n2026-01-05,North,50,5\n2026-01-06,South,60,6\n2026-01-07,North,70,7\n2026-01-08,South,80,8\n2026-01-09,North,90,9\n2026-01-10,South,100,10\n"
    response = client.post("/upload", files={"file": ("sales.csv", payload, "text/csv")})
    assert response.status_code == 201
    return response.json()["dataset_id"]


def get_record_count(model) -> int:
    session = new_session()
    try:
        return session.query(model).count()
    finally:
        session.close()


def test_db_initializes_and_default_workspace_exists(client: TestClient) -> None:
    client.get("/health")
    workspace = new_session().query(Workspace).filter(Workspace.slug == DEFAULT_WORKSPACE_SLUG).one_or_none()

    assert workspace is not None
    assert workspace.name == "Default Workspace"


def test_upload_creates_dataset_record(client: TestClient) -> None:
    dataset_id = upload_csv(client)

    session = new_session()
    try:
        record = session.query(DatasetRecord).filter(DatasetRecord.dataset_id == dataset_id).one_or_none()
        assert record is not None
        assert record.original_filename == "sales.csv"
        assert record.row_count == 10
    finally:
        session.close()


def test_dataset_listing_reads_db_records(client: TestClient) -> None:
    dataset_id = upload_csv(client)
    metadata_path = Path(paths.DATASETS_DIR) / dataset_id / "metadata.json"
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload["original_filename"] = "changed-on-disk.csv"
    metadata_path.write_text(json.dumps(payload), encoding="utf-8")

    response = client.get("/datasets")

    assert response.status_code == 200
    assert response.json()[0]["original_filename"] == "sales.csv"


def test_dataset_detail_reads_db_record(client: TestClient) -> None:
    dataset_id = upload_csv(client)
    metadata_path = Path(paths.DATASETS_DIR) / dataset_id / "metadata.json"
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    payload["original_filename"] = "changed-on-disk.csv"
    metadata_path.write_text(json.dumps(payload), encoding="utf-8")

    response = client.get(f"/datasets/{dataset_id}")

    assert response.status_code == 200
    assert response.json()["original_filename"] == "sales.csv"


def test_analysis_creates_analysis_record(client: TestClient) -> None:
    dataset_id = upload_csv(client)
    response = client.post(f"/datasets/{dataset_id}/analyze")

    assert response.status_code == 200
    session = new_session()
    try:
        record = session.query(AnalysisRecord).filter(AnalysisRecord.dataset_id == dataset_id).one_or_none()
        assert record is not None
        assert record.row_count == 10
        assert record.chart_count > 0
    finally:
        session.close()


def test_forecast_creates_forecast_record(client: TestClient) -> None:
    dataset_id = upload_csv(client)
    response = client.post(
        f"/datasets/{dataset_id}/forecast",
        json={"date_column": "date", "target_column": "sales", "periods": 3, "frequency": "D", "model": "auto"},
    )

    assert response.status_code == 200
    assert get_record_count(ForecastRecord) == 1


def test_report_creates_report_record_and_download_uses_record(client: TestClient) -> None:
    dataset_id = upload_csv(client)
    assert client.post(f"/datasets/{dataset_id}/analyze").status_code == 200
    report_response = client.post(
        f"/datasets/{dataset_id}/report",
        json={"format": "html", "include_forecast": False, "include_charts": True, "include_chat_summary": False},
    )
    assert report_response.status_code == 200
    report_id = report_response.json()["report_id"]

    assert get_record_count(ReportRecord) == 1
    download = client.get(f"/datasets/{dataset_id}/reports/{report_id}/download")
    assert download.status_code == 200
    assert "Dataset Intelligence Report" in download.text


def test_filesystem_fallback_works_when_dataset_record_missing(client: TestClient) -> None:
    dataset_id = upload_csv(client)
    assert delete_dataset_record(dataset_id)

    response = client.get(f"/datasets/{dataset_id}")

    assert response.status_code == 200
    assert response.json()["dataset_id"] == dataset_id


def test_sync_filesystem_to_db_imports_existing_metadata(client: TestClient) -> None:
    metadata = DatasetMetadata(
        dataset_id="filesystemonly123",
        original_filename="legacy.csv",
        stored_filename="original.csv",
        file_size_bytes=18,
        content_type="text/csv",
        created_at="2026-01-01T00:00:00+00:00",
        row_count=1,
        column_count=2,
        columns=["a", "b"],
    )
    dataset_dir = storage_service.create_dataset_dir(metadata.dataset_id)
    (dataset_dir / storage_service.ORIGINAL_FILENAME).write_text("a,b\n1,2\n", encoding="utf-8")
    storage_service.save_metadata(metadata)
    delete_dataset_record(metadata.dataset_id)

    summary = sync_filesystem_to_db()

    assert summary["datasets"] >= 1
    session = new_session()
    try:
        record = session.query(DatasetRecord).filter(DatasetRecord.dataset_id == metadata.dataset_id).one_or_none()
        assert record is not None
        assert record.original_filename == "legacy.csv"
    finally:
        session.close()
