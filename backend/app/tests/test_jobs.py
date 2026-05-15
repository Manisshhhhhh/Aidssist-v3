from __future__ import annotations

import os
import subprocess
import sys

from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.core.config import get_settings
from app.db.session import get_engine
from app.repositories import job_repository
from app.services.job_runner import run_next_job_once


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
    monkeypatch.setenv("AIDSSIST_JWT_SECRET_KEY", "dev-only-long-random-secret-for-job-tests")
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


def upload_dataset(client: TestClient, headers: dict[str, str] | None = None, workspace_id: int | None = None) -> str:
    url = "/upload"
    if workspace_id is not None:
        url = f"{url}?workspace_id={workspace_id}"
    response = client.post(url, files=CSV_FILE, headers=headers or {})
    assert response.status_code == 201
    return response.json()["dataset_id"]


def first_workspace_id(client: TestClient, token: str) -> int:
    response = client.get("/workspaces", headers=auth_header(token))
    assert response.status_code == 200
    return response.json()[0]["id"]


def test_jobs_migration_table_exists(client: TestClient) -> None:
    inspector = inspect(get_engine())

    assert "jobs" in inspector.get_table_names()


def test_alembic_upgrade_head_includes_jobs_table(tmp_path) -> None:
    db_path = tmp_path / "jobs_alembic.db"
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
    assert db_path.is_file()


def test_create_get_claim_and_mark_job(client: TestClient) -> None:
    record = job_repository.create_job("analysis", {"dataset_id": "abc"}, workspace_id=1, dataset_id="abc")

    loaded = job_repository.get_job(record.job_id)
    claimed = job_repository.claim_next_queued_job()
    succeeded = job_repository.mark_succeeded(record.job_id, {"ok": True})

    assert loaded is not None
    assert claimed is not None
    assert claimed.status == "running"
    assert succeeded is not None
    assert succeeded.status == "succeeded"
    assert succeeded.progress == 100


def test_failed_job_stores_sanitized_error(client: TestClient) -> None:
    record = job_repository.create_job("analysis", {"dataset_id": "abc"}, workspace_id=1, dataset_id="abc")

    failed = job_repository.mark_failed(record.job_id, "  bad\n\nerror " * 100)

    assert failed is not None
    assert failed.status == "failed"
    assert "\n" not in (failed.error_message or "")
    assert len(failed.error_message or "") <= 500


def test_worker_once_processes_queued_analysis_job(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    response = client.post(f"/datasets/{dataset_id}/analyze?async=true")
    job_id = response.json()["job_id"]

    processed = run_next_job_once()
    status_response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 202
    assert processed is not None
    assert processed.status == "succeeded"
    assert status_response.json()["output"]["dataset_id"] == dataset_id


def test_analysis_endpoint_sync_behavior_unchanged(client: TestClient) -> None:
    dataset_id = upload_dataset(client)

    response = client.post(f"/datasets/{dataset_id}/analyze")

    assert response.status_code == 200
    assert response.json()["dataset_id"] == dataset_id
    assert "row_count" in response.json()


def test_forecast_endpoint_async_returns_job(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    response = client.post(
        f"/datasets/{dataset_id}/forecast?async=true",
        json={"date_column": "date", "target_column": "sales", "periods": 3, "frequency": "D", "model": "auto"},
    )

    assert response.status_code == 202
    assert response.json()["job_type"] == "forecast"


def test_report_endpoint_async_returns_job(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    client.post(f"/datasets/{dataset_id}/analyze")
    response = client.post(
        f"/datasets/{dataset_id}/report?async=true",
        json={"format": "html", "include_forecast": False, "include_charts": True, "include_chat_summary": False},
    )

    assert response.status_code == 202
    assert response.json()["job_type"] == "report"


def test_get_job_status_and_cancel_queued_job(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    created = client.post(f"/datasets/{dataset_id}/analyze?async=true")
    job_id = created.json()["job_id"]

    status_response = client.get(f"/jobs/{job_id}")
    cancelled = client.post(f"/jobs/{job_id}/cancel")

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "queued"
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_running_job_cannot_be_cancelled(client: TestClient) -> None:
    record = job_repository.create_job("analysis", {"dataset_id": "abc"}, workspace_id=1, dataset_id="abc")
    claimed = job_repository.claim_next_queued_job()

    response = client.post(f"/jobs/{record.job_id}/cancel")

    assert claimed is not None
    assert response.status_code == 400


def test_auth_disabled_job_listing_works(client: TestClient) -> None:
    job_repository.create_job("analysis", {"dataset_id": "abc"}, workspace_id=1, dataset_id="abc")

    response = client.get("/jobs")

    assert response.status_code == 200
    assert response.json()["jobs"]


def test_workspace_member_job_visibility(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    _, viewer_token = register_and_login(client, "viewer@example.com")
    _, outsider_token = register_and_login(client, "outsider@example.com")
    workspace_id = first_workspace_id(client, owner_token)
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": "viewer@example.com", "role": "viewer"},
        headers=auth_header(owner_token),
    )
    dataset_id = upload_dataset(client, headers=auth_header(owner_token), workspace_id=workspace_id)
    created = client.post(f"/datasets/{dataset_id}/analyze?async=true", headers=auth_header(owner_token))
    job_id = created.json()["job_id"]

    viewer_response = client.get(f"/jobs/{job_id}", headers=auth_header(viewer_token))
    outsider_response = client.get(f"/jobs/{job_id}", headers=auth_header(outsider_token))

    assert viewer_response.status_code == 200
    assert outsider_response.status_code == 404
