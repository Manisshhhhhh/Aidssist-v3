from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.llm.base import LLMResult
from app.llm.gemini_provider import GeminiProviderError
from app.models.llm_models import AiSummaryRequest
from app.repositories import artifact_repository
from app.db.models import User
from app.db.session import new_session
from app.services.llm_prompt_service import build_ai_summary_prompt
from app.services.analysis_service import load_analysis
from app.services.storage_service import load_metadata


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


class FakeProvider:
    def generate_text(self, system_instruction, prompt, max_output_tokens=None, temperature=None):  # noqa: ANN001
        assert "raw_csv_rows_sent" in prompt
        return LLMResult(
            text="The dataset has clear regional sales trends grounded in deterministic outputs.",
            provider="gemini",
            model="gemini-2.5-flash",
            input_chars=len(system_instruction) + len(prompt),
            output_chars=74,
            finish_reason="STOP",
            raw_metadata={"finish_reason": "STOP"},
        )


class FailingProvider:
    def generate_text(self, system_instruction, prompt, max_output_tokens=None, temperature=None):  # noqa: ANN001
        raise GeminiProviderError("secret API key exploded")


def upload_dataset(client: TestClient, headers: dict[str, str] | None = None, workspace_id: int | None = None) -> str:
    url = "/upload"
    if workspace_id is not None:
        url = f"{url}?workspace_id={workspace_id}"
    response = client.post(url, files=CSV_FILE, headers=headers or {})
    assert response.status_code == 201
    return response.json()["dataset_id"]


def analyze_dataset(client: TestClient, dataset_id: str, headers: dict[str, str] | None = None) -> None:
    response = client.post(f"/datasets/{dataset_id}/analyze", headers=headers or {})
    assert response.status_code == 200


def enable_llm(monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_LLM_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    get_settings.cache_clear()


def enable_user_auth(monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_USER_AUTH_ENABLED", "true")
    monkeypatch.setenv("AIDSSIST_JWT_SECRET_KEY", "dev-only-long-random-secret-for-llm-tests")
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


def make_admin(user_id: int) -> None:
    session = new_session()
    try:
        user = session.query(User).filter(User.id == user_id).one()
        user.is_admin = True
        session.commit()
    finally:
        session.close()


def test_ai_summary_returns_503_when_llm_disabled(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    analyze_dataset(client, dataset_id)

    response = client.post(f"/datasets/{dataset_id}/ai-summary", json={})

    assert response.status_code == 503
    assert response.json()["detail"] == "LLM features are disabled."


def test_report_with_ai_summary_disabled_includes_note(client: TestClient) -> None:
    dataset_id = upload_dataset(client)
    analyze_dataset(client, dataset_id)

    response = client.post(
        f"/datasets/{dataset_id}/report",
        json={"format": "html", "include_ai_summary": True},
    )
    report = response.json()
    download = client.get(report["download_url"])

    assert response.status_code == 200
    assert "LLM features are disabled." in download.text


def test_ai_summary_succeeds_with_mocked_provider(client: TestClient, monkeypatch) -> None:
    enable_llm(monkeypatch)
    monkeypatch.setattr("app.services.llm_service.get_llm_provider", lambda: FakeProvider())
    dataset_id = upload_dataset(client)
    analyze_dataset(client, dataset_id)

    response = client.post(
        f"/datasets/{dataset_id}/ai-summary",
        json={"include_forecast": False, "include_charts": True, "tone": "executive", "format": "bullets"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["provider"] == "gemini"
    assert payload["grounding"]["used_analysis"] is True
    assert payload["grounding"]["raw_rows_sent"] is False
    assert artifact_repository.latest_dataset_artifact(dataset_id, "ai_summary_json") is not None


def test_ai_summary_requires_analysis(client: TestClient, monkeypatch) -> None:
    enable_llm(monkeypatch)
    monkeypatch.setattr("app.services.llm_service.get_llm_provider", lambda: FakeProvider())
    dataset_id = upload_dataset(client)

    response = client.post(f"/datasets/{dataset_id}/ai-summary", json={})

    assert response.status_code == 400
    assert "Run analysis" in response.json()["detail"]


def test_missing_gemini_key_returns_503(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_LLM_ENABLED", "true")
    get_settings.cache_clear()
    dataset_id = upload_dataset(client)
    analyze_dataset(client, dataset_id)

    response = client.post(f"/datasets/{dataset_id}/ai-summary", json={})

    assert response.status_code == 503
    assert response.json()["detail"] == "Gemini API key is not configured."


def test_ai_summary_respects_workspace_permissions(client: TestClient, monkeypatch) -> None:
    enable_user_auth(monkeypatch)
    enable_llm(monkeypatch)
    monkeypatch.setattr("app.services.llm_service.get_llm_provider", lambda: FakeProvider())
    _, owner_token = register_and_login(client, "owner@example.com")
    _, outsider_token = register_and_login(client, "outsider@example.com")
    workspace_id = first_workspace_id(client, owner_token)
    dataset_id = upload_dataset(client, headers=auth_header(owner_token), workspace_id=workspace_id)
    analyze_dataset(client, dataset_id, headers=auth_header(owner_token))

    allowed = client.post(f"/datasets/{dataset_id}/ai-summary", json={}, headers=auth_header(owner_token))
    denied = client.post(f"/datasets/{dataset_id}/ai-summary", json={}, headers=auth_header(outsider_token))

    assert allowed.status_code == 200
    assert denied.status_code == 404


def test_prompt_builder_uses_deterministic_outputs_not_raw_csv_rows(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_LLM_MAX_INPUT_CHARS", "1200")
    get_settings.cache_clear()
    dataset_id = upload_dataset(client)
    analyze_dataset(client, dataset_id)
    metadata = load_metadata(dataset_id)
    analysis = load_analysis(dataset_id)
    assert metadata is not None and analysis is not None

    prompt, grounding = build_ai_summary_prompt(metadata, analysis, request=AiSummaryRequest())

    assert "2026-01-01,North,10,1" not in prompt
    assert len(prompt) <= 1255
    assert grounding["used_analysis"] is True


def test_gemini_errors_are_sanitized(client: TestClient, monkeypatch) -> None:
    enable_llm(monkeypatch)
    monkeypatch.setattr("app.services.llm_service.get_llm_provider", lambda: FailingProvider())
    dataset_id = upload_dataset(client)
    analyze_dataset(client, dataset_id)

    response = client.post(f"/datasets/{dataset_id}/ai-summary", json={})

    assert response.status_code == 502
    assert response.json()["detail"] == "Gemini summary generation failed."
    assert "secret" not in response.text.lower()


def test_ai_summary_audit_events_created(client: TestClient, monkeypatch) -> None:
    enable_llm(monkeypatch)
    monkeypatch.setattr("app.services.llm_service.get_llm_provider", lambda: FakeProvider())
    dataset_id = upload_dataset(client)
    analyze_dataset(client, dataset_id)
    client.post(f"/datasets/{dataset_id}/ai-summary", json={})

    response = client.get("/audit/events?event_type=llm.summary.succeeded")

    assert response.status_code == 200
    assert response.json()["events"]
    metadata = response.json()["events"][0]["metadata"]
    assert "prompt" not in metadata
    assert metadata["input_chars"] > 0


def test_diagnostics_reports_key_configured_without_exposing_key(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("AIDSSIST_LLM_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-diagnostic-key")
    get_settings.cache_clear()

    response = client.get("/diagnostics/system")

    assert response.status_code == 200
    assert response.json()["llm_enabled"] is True
    assert response.json()["llm_key_configured"] is True
    assert "test-diagnostic-key" not in response.text
