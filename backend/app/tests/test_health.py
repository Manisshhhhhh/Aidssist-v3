from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cors_allows_local_macos_browser_origin() -> None:
    client = TestClient(app)

    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_allows_live_vercel_frontend_origin() -> None:
    client = TestClient(app)

    response = client.get("/health", headers={"Origin": "https://aidssist-v3.vercel.app"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://aidssist-v3.vercel.app"
