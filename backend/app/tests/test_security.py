from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.rate_limit import clear_rate_limit_state


CSV_FILE = {"file": ("sales.csv", b"date,sales\n2026-01-01,10\n", "text/csv")}


def enable_auth(monkeypatch, api_key: str = "demo-secret") -> None:
    monkeypatch.setenv("AIDSSIST_AUTH_ENABLED", "true")
    monkeypatch.setenv("AIDSSIST_API_KEY", api_key)
    get_settings.cache_clear()


def test_health_works_without_api_key_when_auth_enabled(client: TestClient, monkeypatch) -> None:
    enable_auth(monkeypatch)

    response = client.get("/health")

    assert response.status_code == 200


def test_protected_endpoint_works_when_auth_disabled(client: TestClient) -> None:
    response = client.get("/datasets")

    assert response.status_code == 200


def test_protected_endpoint_returns_401_when_key_missing(client: TestClient, monkeypatch) -> None:
    enable_auth(monkeypatch)

    response = client.get("/datasets")

    assert response.status_code == 401
    assert response.json()["detail"] == "This Aidssist server requires an API key."


def test_protected_endpoint_returns_401_when_key_invalid(client: TestClient, monkeypatch) -> None:
    enable_auth(monkeypatch)

    response = client.get("/datasets", headers={"X-Aidssist-API-Key": "wrong"})

    assert response.status_code == 401


def test_protected_endpoint_works_when_key_valid(client: TestClient, monkeypatch) -> None:
    enable_auth(monkeypatch)

    response = client.get("/datasets", headers={"X-Aidssist-API-Key": "demo-secret"})

    assert response.status_code == 200


def test_security_headers_exist_on_responses(client: TestClient) -> None:
    response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "camera=()" in response.headers["Permissions-Policy"]
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_frontend_cors_defaults_include_dev_and_docker_origins() -> None:
    settings = get_settings()

    assert "http://127.0.0.1:5173" in settings.cors_origins
    assert "http://localhost:5173" in settings.cors_origins
    assert "http://127.0.0.1:8080" in settings.cors_origins
    assert "http://localhost:8080" in settings.cors_origins
    assert "https://aidssist-v3.vercel.app" in settings.cors_origins


def test_cors_origins_accept_plain_url_env(monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_CORS_ORIGINS", "https://aidssist-v3.vercel.app")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.cors_origins == ["https://aidssist-v3.vercel.app"]
    get_settings.cache_clear()


def test_rate_limiter_returns_429_when_limit_exceeded(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("AIDSSIST_RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("AIDSSIST_RATE_LIMIT_WINDOW_SECONDS", "60")
    get_settings.cache_clear()
    clear_rate_limit_state()

    first = client.post("/upload", files=CSV_FILE)
    second = client.post("/upload", files=CSV_FILE)

    assert first.status_code == 201
    assert second.status_code == 429
    assert "Rate limit exceeded" in second.json()["detail"]


def test_rate_limiter_can_be_disabled(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("AIDSSIST_RATE_LIMIT_REQUESTS", "1")
    get_settings.cache_clear()
    clear_rate_limit_state()

    first = client.post("/upload", files=CSV_FILE)
    second = client.post("/upload", files=CSV_FILE)

    assert first.status_code == 201
    assert second.status_code == 201


def test_upload_max_size_configuration_uses_new_env_name(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_MAX_UPLOAD_MB", "1")
    get_settings.cache_clear()

    content = b"a,b\n" + (b"1,2\n" * ((1024 * 1024 // 4) + 2))
    response = client.post("/upload", files={"file": ("large.csv", content, "text/csv")})

    assert response.status_code == 400
    assert "1MB" in response.json()["detail"]


def test_path_traversal_dataset_id_does_not_expose_paths(client: TestClient) -> None:
    response = client.get("/datasets/..%2F..%2Fetc%2Fpasswd")

    assert response.status_code in {404, 400}
    assert "/Users/" not in response.text
    assert "Desktop" not in response.text


def test_path_traversal_chart_id_does_not_expose_paths(client: TestClient) -> None:
    upload = client.post("/upload", files=CSV_FILE)
    dataset_id = upload.json()["dataset_id"]
    client.post(f"/datasets/{dataset_id}/analyze")

    response = client.get(f"/datasets/{dataset_id}/charts/..%2Fsecret/data")

    assert response.status_code in {404, 400}
    assert "/Users/" not in response.text


def test_path_like_report_id_returns_404(client: TestClient) -> None:
    upload = client.post("/upload", files=CSV_FILE)
    dataset_id = upload.json()["dataset_id"]

    response = client.get(f"/datasets/{dataset_id}/reports/..%2Fsecret/download")

    assert response.status_code in {404, 400}
    assert "/Users/" not in response.text
