from __future__ import annotations

import os
import subprocess
import sys

from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.core.config import get_settings
from app.db.models import AuditLogRecord, User
from app.db.session import get_engine, new_session
from app.repositories import job_repository
from app.services.audit_service import sanitize_metadata
from app.services.job_runner import run_next_job_once


CSV_FILE = {
    "file": (
        "sales.csv",
        b"date,region,sales,profit\n"
        b"2026-01-01,North,10,1\n"
        b"2026-01-02,South,20,2\n"
        b"2026-01-03,North,30,3\n"
        b"2026-01-04,South,40,4\n"
        b"2026-01-05,North,50,5\n"
        b"2026-01-06,South,60,6\n"
        b"2026-01-07,North,70,7\n"
        b"2026-01-08,South,80,8\n"
        b"2026-01-09,North,90,9\n"
        b"2026-01-10,South,100,10\n",
        "text/csv",
    )
}


def upload_dataset(client: TestClient, headers: dict[str, str] | None = None, workspace_id: int | None = None) -> str:
    url = "/upload"
    if workspace_id is not None:
        url = f"{url}?workspace_id={workspace_id}"
    response = client.post(url, files=CSV_FILE, headers=headers or {})
    assert response.status_code == 201
    return response.json()["dataset_id"]


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


def enable_user_auth(monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_USER_AUTH_ENABLED", "true")
    monkeypatch.setenv("AIDSSIST_JWT_SECRET_KEY", "dev-only-long-random-secret-for-audit-tests")
    get_settings.cache_clear()


def make_admin(user_id: int) -> None:
    session = new_session()
    try:
        user = session.query(User).filter(User.id == user_id).one()
        user.is_admin = True
        session.commit()
    finally:
        session.close()


def events(event_type: str | None = None) -> list[AuditLogRecord]:
    session = new_session()
    try:
        query = session.query(AuditLogRecord)
        if event_type:
            query = query.filter(AuditLogRecord.event_type == event_type)
        return query.order_by(AuditLogRecord.created_at.desc()).all()
    finally:
        session.close()


def test_request_id_headers_are_added_and_safe_client_ids_are_preserved(client: TestClient) -> None:
    generated = client.get("/health")
    supplied = client.get("/health", headers={"X-Request-ID": "safe-request-123"})
    invalid = client.get("/health", headers={"X-Request-ID": "../bad"})

    assert generated.headers["X-Request-ID"]
    assert supplied.headers["X-Request-ID"] == "safe-request-123"
    assert invalid.headers["X-Request-ID"] != "../bad"


def test_security_headers_still_exist(client: TestClient) -> None:
    response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_audit_migration_table_exists(client: TestClient) -> None:
    assert "audit_logs" in inspect(get_engine()).get_table_names()


def test_alembic_upgrade_head_includes_audit_table(tmp_path) -> None:
    db_path = tmp_path / "audit_alembic.db"
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


def test_auth_register_login_success_and_failure_create_audit_events(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    client.post(
        "/auth/register",
        json={"email": "audit@example.com", "password": "strong-password", "full_name": "Audit User"},
    )
    client.post("/auth/login", json={"email": "audit@example.com", "password": "strong-password"})
    client.post("/auth/login", json={"email": "audit@example.com", "password": "wrong"})

    login_events = events("auth.login")
    register_events = events("auth.register")

    assert register_events and register_events[0].outcome == "success"
    assert {event.outcome for event in login_events} >= {"success", "failure"}


def test_dataset_analysis_forecast_chat_report_artifact_and_job_audit_events(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    analysis = client.post(f"/datasets/{dataset_id}/analyze").json()
    chart_id = analysis["recommended_charts"][0]["chart_id"]
    client.get(f"/datasets/{dataset_id}/charts/{chart_id}/data")
    client.post(
        f"/datasets/{dataset_id}/forecast",
        json={"date_column": "date", "target_column": "sales", "periods": 3, "frequency": "D", "model": "auto"},
    )
    client.post(f"/datasets/{dataset_id}/chat", json={"message": "average sales by region"})
    report = client.post(
        f"/datasets/{dataset_id}/report",
        json={"format": "html", "include_forecast": True, "include_charts": True, "include_chat_summary": False},
    ).json()
    client.get(report["download_url"])
    artifact = client.get(f"/datasets/{dataset_id}/artifacts").json()["artifacts"][0]
    client.get(artifact["download_url"])
    job = client.post(f"/datasets/{dataset_id}/analyze?async=true").json()
    client.post(f"/jobs/{job['job_id']}/cancel")

    event_types = {event.event_type for event in events()}

    assert {
        "dataset.upload",
        "analysis.run",
        "forecast.run",
        "chat.ask",
        "report.generate",
        "report.download",
        "artifact.download",
        "job.create",
        "job.cancelled",
    }.issubset(event_types)


def test_job_success_and_failure_audit_events(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    client.post(f"/datasets/{dataset_id}/analyze?async=true")
    run_next_job_once()
    job_repository.create_job("analysis", {"dataset_id": "missing"}, workspace_id=1, dataset_id="missing")
    run_next_job_once()

    event_types = {event.event_type for event in events()}

    assert "job.succeeded" in event_types
    assert "job.failed" in event_types


def test_audit_api_paginates_and_returns_events(client: TestClient) -> None:
    upload_dataset(client)

    response = client.get("/audit/events?limit=1&offset=0")

    assert response.status_code == 200
    assert response.json()["limit"] == 1
    assert len(response.json()["events"]) == 1


def test_audit_metadata_redacts_secrets() -> None:
    metadata = sanitize_metadata(
        {"password": "secret", "nested": {"api_key": "abc", "safe": "ok"}, "items": [{"jwt_token": "bad"}]}
    )

    assert metadata["password"] == "[redacted]"
    assert metadata["nested"]["api_key"] == "[redacted]"
    assert metadata["nested"]["safe"] == "ok"
    assert metadata["items"][0]["jwt_token"] == "[redacted]"


def test_workspace_audit_events_and_permissions(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    viewer, viewer_token = register_and_login(client, "viewer@example.com")
    _, outsider_token = register_and_login(client, "outsider@example.com")
    workspace_id = first_workspace_id(client, owner_token)

    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": "viewer@example.com", "role": "viewer"},
        headers=auth_header(owner_token),
    )
    client.patch(
        f"/workspaces/{workspace_id}/members/{viewer['id']}",
        json={"role": "editor"},
        headers=auth_header(owner_token),
    )
    client.delete(f"/workspaces/{workspace_id}/members/{viewer['id']}", headers=auth_header(owner_token))

    owner_events = client.get(f"/audit/events?workspace_id={workspace_id}", headers=auth_header(owner_token))
    outsider_events = client.get(f"/audit/events?workspace_id={workspace_id}", headers=auth_header(outsider_token))

    assert owner_events.status_code == 200
    assert {"workspace.member.add", "workspace.member.update", "workspace.member.remove"}.issubset(
        {event["event_type"] for event in owner_events.json()["events"]}
    )
    assert outsider_events.status_code == 200
    assert outsider_events.json()["events"] == []


def test_global_admin_can_read_all_audit_events_and_diagnostics_are_admin_only(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    admin, admin_token = register_and_login(client, "admin@example.com")
    _, user_token = register_and_login(client, "user@example.com")
    make_admin(admin["id"])

    user_diagnostics = client.get("/diagnostics/system", headers=auth_header(user_token))
    admin_diagnostics = client.get("/diagnostics/system", headers=auth_header(admin_token))
    admin_events = client.get("/audit/events", headers=auth_header(admin_token))

    assert user_diagnostics.status_code == 403
    assert admin_diagnostics.status_code == 200
    assert admin_diagnostics.json()["database_type"] == "sqlite"
    assert admin_events.status_code == 200
    assert admin_events.json()["events"]


def test_rate_limit_creates_security_audit_event(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("AIDSSIST_RATE_LIMIT_WINDOW_SECONDS", "60")
    get_settings.cache_clear()

    client.post("/upload", files=CSV_FILE)
    limited = client.post("/upload", files=CSV_FILE)

    assert limited.status_code == 429
    assert events("security.rate_limited")
