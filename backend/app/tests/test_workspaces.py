from __future__ import annotations

import os
import subprocess
import sys

from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.core.config import get_settings
from app.db.session import get_engine


CSV_FILE = {"file": ("sales.csv", b"date,sales\n2026-01-01,10\n2026-01-02,20\n", "text/csv")}


def enable_user_auth(monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_USER_AUTH_ENABLED", "true")
    monkeypatch.setenv("AIDSSIST_JWT_SECRET_KEY", "dev-only-long-random-secret-for-workspace-tests")
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


def test_alembic_upgrade_head_works_on_temp_sqlite_db(tmp_path) -> None:
    db_path = tmp_path / "alembic.db"
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


def test_migrated_schema_contains_current_tables(client: TestClient) -> None:
    inspector = inspect(get_engine())

    assert {"users", "workspaces", "workspace_members", "datasets", "reports"}.issubset(
        set(inspector.get_table_names())
    )


def test_registering_user_creates_personal_workspace_and_owner_membership(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    user, token = register_and_login(client, "owner@example.com")

    response = client.get("/workspaces", headers=auth_header(token))

    assert response.status_code == 200
    assert response.json()[0]["current_user_role"] == "owner"
    assert "owner" in response.json()[0]["name"]
    members = client.get(f"/workspaces/{response.json()[0]['id']}/members", headers=auth_header(token))
    assert members.status_code == 200
    assert members.json()[0]["user_id"] == user["id"]


def test_user_can_create_workspace(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, token = register_and_login(client, "owner@example.com")

    response = client.post("/workspaces", json={"name": "Analytics Team"}, headers=auth_header(token))

    assert response.status_code == 201
    assert response.json()["name"] == "Analytics Team"
    assert response.json()["current_user_role"] == "owner"


def test_owner_can_add_existing_user_as_viewer_or_editor(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    viewer, _ = register_and_login(client, "viewer@example.com")
    workspace_id = first_workspace_id(client, owner_token)

    add_viewer = client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": "viewer@example.com", "role": "viewer"},
        headers=auth_header(owner_token),
    )
    add_editor = client.patch(
        f"/workspaces/{workspace_id}/members/{viewer['id']}",
        json={"role": "editor"},
        headers=auth_header(owner_token),
    )

    assert add_viewer.status_code == 200
    assert add_viewer.json()["role"] == "viewer"
    assert add_editor.status_code == 200
    assert add_editor.json()["role"] == "editor"


def test_viewer_cannot_upload_to_workspace(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    _, viewer_token = register_and_login(client, "viewer@example.com")
    workspace_id = first_workspace_id(client, owner_token)
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": "viewer@example.com", "role": "viewer"},
        headers=auth_header(owner_token),
    )

    response = client.post(f"/upload?workspace_id={workspace_id}", files=CSV_FILE, headers=auth_header(viewer_token))

    assert response.status_code == 403


def test_editor_can_upload_to_workspace(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    _, editor_token = register_and_login(client, "editor@example.com")
    workspace_id = first_workspace_id(client, owner_token)
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": "editor@example.com", "role": "editor"},
        headers=auth_header(owner_token),
    )

    response = client.post(f"/upload?workspace_id={workspace_id}", files=CSV_FILE, headers=auth_header(editor_token))

    assert response.status_code == 201
    assert response.json()["workspace_id"] == workspace_id


def test_viewer_can_view_dataset_chart_and_report_download(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    _, viewer_token = register_and_login(client, "viewer@example.com")
    workspace_id = first_workspace_id(client, owner_token)
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": "viewer@example.com", "role": "viewer"},
        headers=auth_header(owner_token),
    )
    dataset_id = client.post(f"/upload?workspace_id={workspace_id}", files=CSV_FILE, headers=auth_header(owner_token)).json()["dataset_id"]
    analysis = client.post(f"/datasets/{dataset_id}/analyze", headers=auth_header(owner_token)).json()
    chart_id = analysis["recommended_charts"][0]["chart_id"]
    report = client.post(
        f"/datasets/{dataset_id}/report",
        json={"format": "html", "include_forecast": False, "include_charts": True, "include_chat_summary": False},
        headers=auth_header(owner_token),
    ).json()

    detail = client.get(f"/datasets/{dataset_id}", headers=auth_header(viewer_token))
    chart = client.get(f"/datasets/{dataset_id}/charts/{chart_id}/data", headers=auth_header(viewer_token))
    download = client.get(report["download_url"], headers=auth_header(viewer_token))

    assert detail.status_code == 200
    assert chart.status_code == 200
    assert download.status_code == 200


def test_viewer_cannot_run_write_actions(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    _, viewer_token = register_and_login(client, "viewer@example.com")
    workspace_id = first_workspace_id(client, owner_token)
    client.post(
        f"/workspaces/{workspace_id}/members",
        json={"email": "viewer@example.com", "role": "viewer"},
        headers=auth_header(owner_token),
    )
    dataset_id = client.post(f"/upload?workspace_id={workspace_id}", files=CSV_FILE, headers=auth_header(owner_token)).json()["dataset_id"]

    analyze = client.post(f"/datasets/{dataset_id}/analyze", headers=auth_header(viewer_token))
    forecast = client.post(
        f"/datasets/{dataset_id}/forecast",
        json={"date_column": "date", "target_column": "sales", "periods": 2, "frequency": "D", "model": "auto"},
        headers=auth_header(viewer_token),
    )
    report = client.post(
        f"/datasets/{dataset_id}/report",
        json={"format": "html", "include_forecast": False, "include_charts": True, "include_chat_summary": False},
        headers=auth_header(viewer_token),
    )

    assert analyze.status_code == 404
    assert forecast.status_code == 404
    assert report.status_code == 404


def test_non_member_cannot_see_workspace_datasets_or_detail(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    _, other_token = register_and_login(client, "other@example.com")
    workspace_id = first_workspace_id(client, owner_token)
    dataset_id = client.post(f"/upload?workspace_id={workspace_id}", files=CSV_FILE, headers=auth_header(owner_token)).json()["dataset_id"]

    listing = client.get(f"/datasets?workspace_id={workspace_id}", headers=auth_header(other_token))
    detail = client.get(f"/datasets/{dataset_id}", headers=auth_header(other_token))

    assert listing.status_code == 200
    assert listing.json() == []
    assert detail.status_code == 404


def test_global_admin_can_access_workspace_dataset(client: TestClient, monkeypatch) -> None:
    from app.repositories.user_repository import set_user_admin

    enable_user_auth(monkeypatch)
    _, owner_token = register_and_login(client, "owner@example.com")
    admin, admin_token = register_and_login(client, "admin@example.com")
    set_user_admin(admin["id"], True)
    workspace_id = first_workspace_id(client, owner_token)
    dataset_id = client.post(f"/upload?workspace_id={workspace_id}", files=CSV_FILE, headers=auth_header(owner_token)).json()["dataset_id"]

    detail = client.get(f"/datasets/{dataset_id}", headers=auth_header(admin_token))

    assert detail.status_code == 200


def test_cannot_remove_or_demote_last_owner(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    owner, owner_token = register_and_login(client, "owner@example.com")
    workspace_id = first_workspace_id(client, owner_token)

    demote = client.patch(
        f"/workspaces/{workspace_id}/members/{owner['id']}",
        json={"role": "admin"},
        headers=auth_header(owner_token),
    )
    remove = client.delete(f"/workspaces/{workspace_id}/members/{owner['id']}", headers=auth_header(owner_token))

    assert demote.status_code == 400
    assert remove.status_code == 400


def test_auth_disabled_returns_default_workspace_and_uploads_to_it(client: TestClient) -> None:
    workspaces = client.get("/workspaces")
    workspace_id = workspaces.json()[0]["id"]
    upload = client.post("/upload", files=CSV_FILE)

    assert workspaces.status_code == 200
    assert workspaces.json()[0]["slug"] == "default"
    assert upload.status_code == 201
    assert upload.json()["workspace_id"] == workspace_id
