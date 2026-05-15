from __future__ import annotations

import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.core.config import get_settings
from app.db.session import get_engine, new_session
from app.db.models import ArtifactRecord
from app.repositories import artifact_repository
from app.services import storage_service
from app.services.artifact_service import audit_artifacts, soft_delete_artifact
from app.storage.base import StorageKeyError
from app.storage.local_storage import LocalStorageProvider


CSV_FILE = {
    "file": (
        "sales.csv",
        b"date,region,sales\n"
        b"2026-01-01,North,10\n"
        b"2026-01-02,South,20\n"
        b"2026-01-03,North,30\n"
        b"2026-01-04,South,40\n"
        b"2026-01-05,North,50\n"
        b"2026-01-06,South,60\n"
        b"2026-01-07,North,70\n"
        b"2026-01-08,South,80\n"
        b"2026-01-09,North,90\n"
        b"2026-01-10,South,100\n",
        "text/csv",
    )
}


def enable_user_auth(monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_USER_AUTH_ENABLED", "true")
    monkeypatch.setenv("AIDSSIST_JWT_SECRET_KEY", "dev-only-long-random-secret-for-artifact-tests")
    get_settings.cache_clear()


def register_and_login(client: TestClient, email: str) -> tuple[dict, str]:
    register = client.post(
        "/auth/register",
        json={"email": email, "password": "strong-password", "full_name": email.split("@")[0]},
    )
    assert register.status_code == 201
    login = client.post("/auth/login", json={"email": email, "password": "strong-password"})
    assert login.status_code == 200
    return register.json(), login.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def first_workspace_id(client: TestClient, token: str) -> int:
    response = client.get("/workspaces", headers=auth_header(token))
    assert response.status_code == 200
    return response.json()[0]["id"]


def upload_dataset(client: TestClient, headers: dict[str, str] | None = None, workspace_id: int | None = None) -> str:
    url = "/upload"
    if workspace_id is not None:
        url = f"{url}?workspace_id={workspace_id}"
    response = client.post(url, files=CSV_FILE, headers=headers or {})
    assert response.status_code == 201
    return response.json()["dataset_id"]


def artifact_types(dataset_id: str) -> set[str]:
    return {artifact.artifact_type for artifact in artifact_repository.list_dataset_artifacts(dataset_id)}


def test_local_storage_save_read_exists_delete_and_list(tmp_path) -> None:
    provider = LocalStorageProvider(tmp_path)

    stored = provider.save_text("datasets/demo/file.txt", "hello", "text/plain")

    assert stored.key == "datasets/demo/file.txt"
    assert provider.exists(stored.key)
    assert provider.read_text(stored.key) == "hello"
    assert len(provider.list("datasets/demo")) == 1
    provider.delete(stored.key)
    assert not provider.exists(stored.key)


def test_local_storage_rejects_path_traversal(tmp_path) -> None:
    provider = LocalStorageProvider(tmp_path)

    with pytest.raises(StorageKeyError):
      provider.save_text("../escape.txt", "bad")


def test_logical_key_maps_under_local_root_only(tmp_path) -> None:
    provider = LocalStorageProvider(tmp_path)

    path = provider.get_local_path("safe/path.txt")

    assert path is not None
    assert path.resolve().is_relative_to(tmp_path.resolve())


def test_artifacts_migration_table_exists(client: TestClient) -> None:
    inspector = inspect(get_engine())

    assert "artifacts" in inspector.get_table_names()


def test_alembic_upgrade_head_includes_artifacts_table(tmp_path) -> None:
    db_path = tmp_path / "artifacts_alembic.db"
    env = os.environ.copy()
    env["AIDSSIST_DATABASE_URL"] = f"sqlite:///{db_path}"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=".",
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr


def test_upload_creates_original_and_metadata_artifacts(client: TestClient) -> None:
    dataset_id = upload_dataset(client)

    assert {"original_csv", "metadata_json"}.issubset(artifact_types(dataset_id))


def test_analysis_forecast_and_report_create_artifacts(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    client.post(f"/datasets/{dataset_id}/analyze")
    client.post(
        f"/datasets/{dataset_id}/forecast",
        json={"date_column": "date", "target_column": "sales", "periods": 3, "frequency": "D", "model": "auto"},
    )
    client.post(
        f"/datasets/{dataset_id}/report",
        json={"format": "html", "include_forecast": True, "include_charts": True, "include_chat_summary": False},
    )

    assert {"analysis_json", "forecast_json", "report_html", "report_json"}.issubset(artifact_types(dataset_id))


def test_dataset_artifacts_endpoint_and_download(client: TestClient) -> None:
    dataset_id = upload_dataset(client)

    response = client.get(f"/datasets/{dataset_id}/artifacts")
    artifact = response.json()["artifacts"][0]
    download = client.get(artifact["download_url"])

    assert response.status_code == 200
    assert "storage_key" not in artifact
    assert download.status_code == 200


def test_non_member_cannot_list_or_download_artifacts(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    _, other_token = register_and_login(client, "other@example.com")
    workspace_id = first_workspace_id(client, owner_token)
    dataset_id = upload_dataset(client, headers=auth_header(owner_token), workspace_id=workspace_id)
    artifact = client.get(f"/datasets/{dataset_id}/artifacts", headers=auth_header(owner_token)).json()["artifacts"][0]

    listing = client.get(f"/datasets/{dataset_id}/artifacts", headers=auth_header(other_token))
    download = client.get(artifact["download_url"], headers=auth_header(other_token))

    assert listing.status_code == 404
    assert download.status_code == 404


def test_viewer_can_list_dataset_artifacts(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    _, viewer_token = register_and_login(client, "viewer@example.com")
    workspace_id = first_workspace_id(client, owner_token)
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": "viewer@example.com", "role": "viewer"},
        headers=auth_header(owner_token),
    )
    dataset_id = upload_dataset(client, headers=auth_header(owner_token), workspace_id=workspace_id)

    response = client.get(f"/datasets/{dataset_id}/artifacts", headers=auth_header(viewer_token))

    assert response.status_code == 200
    assert response.json()["artifacts"]


def test_soft_deleted_artifact_is_not_downloadable(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    artifact = artifact_repository.list_dataset_artifacts(dataset_id)[0]
    soft_delete_artifact(artifact.artifact_id)

    response = client.get(f"/artifacts/{artifact.artifact_id}/download")

    assert response.status_code == 404


def test_storage_audit_detects_missing_storage_object(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    storage_service.get_original_file_path(dataset_id).unlink()

    result = audit_artifacts()

    assert len(result["missing_storage_objects"]) >= 1


def test_sync_filesystem_to_db_creates_artifact_records(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    session = new_session()
    try:
        session.query(ArtifactRecord).delete()
        session.commit()
    finally:
        session.close()

    from scripts.sync_filesystem_to_db import sync_filesystem_to_db

    sync_filesystem_to_db()

    assert {"original_csv", "metadata_json"}.issubset(artifact_types(dataset_id))
