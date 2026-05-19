from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.init_db import validate_auth_configuration
from app.db.models import DatasetRecord
from app.db.session import new_session
from app.repositories.user_repository import set_user_admin


CSV_FILE = {"file": ("sales.csv", b"date,sales\n2026-01-01,10\n2026-01-02,20\n", "text/csv")}


def enable_user_auth(monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_USER_AUTH_ENABLED", "true")
    monkeypatch.setenv("AIDSSIST_JWT_SECRET_KEY", "dev-only-long-random-secret-for-tests")
    get_settings.cache_clear()


def register(client: TestClient, email: str = "user@example.com", password: str = "strong-password") -> dict:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "User Name"},
    )
    assert response.status_code == 201
    return response.json()


def login(client: TestClient, email: str = "user@example.com", password: str = "strong-password") -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_user_succeeds(client: TestClient) -> None:
    payload = register(client, email="Mixed@Example.com")

    assert payload["id"]
    assert payload["email"] == "mixed@example.com"
    assert payload["is_active"] is True
    assert "password" not in payload


def test_duplicate_email_returns_409(client: TestClient) -> None:
    register(client)

    response = client.post(
        "/auth/register",
        json={"email": "USER@example.com", "password": "strong-password", "full_name": "User Name"},
    )

    assert response.status_code == 409


def test_password_shorter_than_8_rejected(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "short", "full_name": "User Name"},
    )

    assert response.status_code == 422


def test_login_succeeds_with_correct_password(client: TestClient) -> None:
    register(client)

    response = client.post("/auth/login", json={"email": "user@example.com", "password": "strong-password"})

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"


def test_login_fails_with_wrong_password(client: TestClient) -> None:
    register(client)

    response = client.post("/auth/login", json={"email": "user@example.com", "password": "wrong-password"})

    assert response.status_code == 401


def test_auth_me_works_with_token(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    register(client)
    token = login(client)

    response = client.get("/auth/me", headers=auth_header(token))

    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_auth_me_rejects_invalid_token(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)

    response = client.get("/auth/me", headers=auth_header("invalid-token"))

    assert response.status_code == 401


def test_health_remains_public_when_user_auth_enabled(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)

    response = client.get("/health")

    assert response.status_code == 200


def test_auth_status_exposes_safe_llm_flags(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_LLM_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-redacted")
    get_settings.cache_clear()

    response = client.get("/auth/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["llm_enabled"] is True
    assert payload["llm_provider"] == "gemini"
    assert payload["llm_model"]
    assert payload["llm_key_configured"] is True
    assert "test-key-redacted" not in response.text
    get_settings.cache_clear()


def test_auth_disabled_keeps_upload_and_list_working(client: TestClient) -> None:
    upload = client.post("/upload", files=CSV_FILE)
    listing = client.get("/datasets")

    assert upload.status_code == 201
    assert listing.status_code == 200
    assert listing.json()


def test_auth_enabled_requires_token_for_upload(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)

    response = client.post("/upload", files=CSV_FILE)

    assert response.status_code == 401


def test_auth_enabled_upload_assigns_owner_user_id(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    user = register(client)
    token = login(client)

    response = client.post("/upload", files=CSV_FILE, headers=auth_header(token))

    assert response.status_code == 201
    dataset_id = response.json()["dataset_id"]
    session = new_session()
    try:
        record = session.query(DatasetRecord).filter(DatasetRecord.dataset_id == dataset_id).one_or_none()
        assert record is not None
        assert record.owner_user_id == user["id"]
    finally:
        session.close()


def test_auth_enabled_dataset_list_only_returns_current_user_datasets(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    register(client, email="one@example.com")
    token_one = login(client, email="one@example.com")
    register(client, email="two@example.com")
    token_two = login(client, email="two@example.com")

    first = client.post("/upload", files=CSV_FILE, headers=auth_header(token_one)).json()["dataset_id"]
    second = client.post(
        "/upload",
        files={"file": ("sales.csv", b"date,sales\n2026-01-01,50\n2026-01-02,60\n", "text/csv")},
        headers=auth_header(token_two),
    ).json()["dataset_id"]

    response = client.get("/datasets", headers=auth_header(token_one))

    ids = [item["dataset_id"] for item in response.json()]
    assert first in ids
    assert second not in ids


def test_user_cannot_access_another_users_dataset(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    register(client, email="one@example.com")
    token_one = login(client, email="one@example.com")
    register(client, email="two@example.com")
    token_two = login(client, email="two@example.com")
    dataset_id = client.post("/upload", files=CSV_FILE, headers=auth_header(token_one)).json()["dataset_id"]

    response = client.get(f"/datasets/{dataset_id}", headers=auth_header(token_two))

    assert response.status_code == 404


def test_admin_can_access_another_users_dataset(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    register(client, email="owner@example.com")
    owner_token = login(client, email="owner@example.com")
    admin = register(client, email="admin@example.com")
    set_user_admin(admin["id"], True)
    admin_token = login(client, email="admin@example.com")
    dataset_id = client.post("/upload", files=CSV_FILE, headers=auth_header(owner_token)).json()["dataset_id"]

    response = client.get(f"/datasets/{dataset_id}", headers=auth_header(admin_token))

    assert response.status_code == 200


def test_api_key_auth_still_works_when_user_auth_disabled(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_AUTH_ENABLED", "true")
    monkeypatch.setenv("AIDSSIST_API_KEY", "demo-key")
    get_settings.cache_clear()

    missing = client.get("/datasets")
    valid = client.get("/datasets", headers={"X-Aidssist-API-Key": "demo-key"})

    assert missing.status_code == 401
    assert valid.status_code == 200


def test_user_auth_enabled_requires_safe_jwt_secret(monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_USER_AUTH_ENABLED", "true")
    monkeypatch.delenv("AIDSSIST_JWT_SECRET_KEY", raising=False)
    get_settings.cache_clear()

    with pytest.raises(RuntimeError):
        validate_auth_configuration()
