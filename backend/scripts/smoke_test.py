from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Any

import requests


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("AIDSSIST_DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'aidssist.db'}")
SAMPLE_FILE = ROOT_DIR / "sample_data" / "sales_timeseries.csv"


class SmokeFailure(Exception):
    """Raised when a smoke-test step fails."""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Aidssist V3 backend smoke test.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Running backend base URL.")
    parser.add_argument("--async-jobs", action="store_true", help="Exercise async analysis/report jobs with the local worker.")
    parser.add_argument("--llm", action="store_true", help="Exercise optional AI summary when LLM env is configured.")
    parser.add_argument("--preflight", action="store_true", help="Exercise diagnostics preflight endpoint.")
    parser.add_argument("--backup", action="store_true", help="Create and download a backup through the API.")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    session = requests.Session()
    api_key = os.getenv("AIDSSIST_API_KEY")
    if api_key:
        session.headers.update({"X-Aidssist-API-Key": api_key})

    try:
        check_health(session, base_url)
        if args.preflight:
            check_preflight(session, base_url)
        workspace_id = authenticate_if_enabled(session, base_url)
        dataset_id = upload_sample(session, base_url, workspace_id)
        analysis = analyze_dataset(session, base_url, dataset_id, async_jobs=args.async_jobs)
        request_first_chart(session, base_url, dataset_id, analysis)
        forecast_dataset(session, base_url, dataset_id)
        ask_chat(session, base_url, dataset_id, "summarize this dataset")
        ask_chat(session, base_url, dataset_id, "average sales by region")
        if args.llm:
            create_ai_summary(session, base_url, dataset_id)
        report = create_report(session, base_url, dataset_id, async_jobs=args.async_jobs)
        download_report(session, base_url, report)
        if args.backup:
            create_and_download_backup(session, base_url)
    except SmokeFailure as exc:
        print(f"FAIL: {exc}")
        return 1
    except requests.RequestException as exc:
        print(f"FAIL: request error: {exc}")
        return 1

    print("PASS: Aidssist V3 smoke test completed.")
    return 0


def check_health(session: requests.Session, base_url: str) -> None:
    response = session.get(f"{base_url}/health", timeout=10)
    expect(response, 200, "health")
    print("PASS: health")


def check_preflight(session: requests.Session, base_url: str) -> None:
    response = session.get(f"{base_url}/diagnostics/preflight", timeout=20)
    expect(response, 200, "preflight")
    status_value = response.json().get("status")
    if status_value not in {"ok", "warning"}:
        raise SmokeFailure(f"preflight returned status {status_value}: {response.text[:300]}")
    print(f"PASS: preflight status={status_value}")


def authenticate_if_enabled(session: requests.Session, base_url: str) -> int | None:
    if os.getenv("AIDSSIST_USER_AUTH_ENABLED", "false").lower() != "true":
        return None

    email = os.getenv("AIDSSIST_SMOKE_EMAIL", "aidssist-smoke@example.com")
    password = os.getenv("AIDSSIST_SMOKE_PASSWORD", "aidssist-smoke-password")
    register_response = session.post(
        f"{base_url}/auth/register",
        json={"email": email, "password": password, "full_name": "Aidssist Smoke"},
        timeout=10,
    )
    if register_response.status_code not in {201, 409}:
        raise SmokeFailure(f"auth register returned {register_response.status_code}: {register_response.text[:300]}")

    login_response = session.post(
        f"{base_url}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    expect(login_response, 200, "auth login")
    token = login_response.json().get("access_token")
    if not token:
        raise SmokeFailure("auth login did not return access_token")
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"PASS: auth user {email}")
    workspaces_response = session.get(f"{base_url}/workspaces", timeout=10)
    expect(workspaces_response, 200, "workspaces")
    workspaces = workspaces_response.json()
    if not workspaces:
        raise SmokeFailure("auth user did not have a workspace")
    workspace_id = int(workspaces[0]["id"])
    print(f"PASS: workspace {workspace_id}")
    return workspace_id


def upload_sample(session: requests.Session, base_url: str, workspace_id: int | None = None) -> str:
    if not SAMPLE_FILE.is_file():
        raise SmokeFailure(f"sample file missing: {SAMPLE_FILE}")

    with SAMPLE_FILE.open("rb") as sample:
        url = f"{base_url}/upload"
        if workspace_id is not None:
            url = f"{url}?workspace_id={workspace_id}"
        response = session.post(
            url,
            files={"file": (SAMPLE_FILE.name, sample, "text/csv")},
            timeout=20,
        )
    expect(response, 201, "upload")
    dataset_id = response.json().get("dataset_id")
    if not dataset_id:
        raise SmokeFailure("upload response did not include dataset_id")
    print(f"PASS: upload dataset_id={dataset_id}")
    return str(dataset_id)


def analyze_dataset(session: requests.Session, base_url: str, dataset_id: str, async_jobs: bool = False) -> dict[str, Any]:
    suffix = "?async=true" if async_jobs else ""
    response = session.post(f"{base_url}/datasets/{dataset_id}/analyze{suffix}", timeout=30)
    if async_jobs:
        expect(response, 202, "analysis job")
        job = process_and_poll_job(session, base_url, response.json()["job_id"])
        payload = job.get("output") or {}
    else:
        expect(response, 200, "analysis")
        payload = response.json()
    if payload.get("row_count", 0) <= 0 or payload.get("column_count", 0) <= 0:
        raise SmokeFailure("analysis returned empty shape")
    print("PASS: analysis")
    return payload


def request_first_chart(session: requests.Session, base_url: str, dataset_id: str, analysis: dict[str, Any]) -> None:
    charts = analysis.get("recommended_charts") or []
    if not charts:
        print("SKIP: chart data, no recommendations")
        return

    chart_id = charts[0]["chart_id"]
    response = session.get(f"{base_url}/datasets/{dataset_id}/charts/{chart_id}/data", timeout=20)
    expect(response, 200, "chart data")
    if "data" not in response.json():
        raise SmokeFailure("chart data response missing data")
    print(f"PASS: chart data chart_id={chart_id}")


def forecast_dataset(session: requests.Session, base_url: str, dataset_id: str) -> None:
    response = session.post(
        f"{base_url}/datasets/{dataset_id}/forecast",
        json={"date_column": "date", "target_column": "sales", "periods": 6, "frequency": "D", "model": "auto"},
        timeout=30,
    )
    expect(response, 200, "forecast")
    if len(response.json().get("forecast_points", [])) != 6:
        raise SmokeFailure("forecast did not return expected period count")
    print("PASS: forecast")


def ask_chat(session: requests.Session, base_url: str, dataset_id: str, message: str) -> None:
    response = session.post(
        f"{base_url}/datasets/{dataset_id}/chat",
        json={"message": message},
        timeout=20,
    )
    expect(response, 200, f"chat: {message}")
    payload = response.json()
    if not payload.get("answer") or payload.get("intent") == "unsupported":
        raise SmokeFailure(f"chat did not answer expected prompt: {message}")
    print(f"PASS: chat '{message}'")


def create_ai_summary(session: requests.Session, base_url: str, dataset_id: str) -> None:
    if os.getenv("AIDSSIST_LLM_ENABLED", "false").lower() != "true" or not os.getenv("GEMINI_API_KEY"):
        print("SKIP: ai summary, LLM disabled or GEMINI_API_KEY not configured")
        return
    response = session.post(
        f"{base_url}/datasets/{dataset_id}/ai-summary",
        json={"include_forecast": True, "include_charts": True, "tone": "executive", "format": "bullets"},
        timeout=45,
    )
    expect(response, 200, "ai summary")
    if not response.json().get("summary"):
        raise SmokeFailure("ai summary response missing summary")
    print("PASS: ai summary")


def create_report(session: requests.Session, base_url: str, dataset_id: str, async_jobs: bool = False) -> dict[str, Any]:
    suffix = "?async=true" if async_jobs else ""
    response = session.post(
        f"{base_url}/datasets/{dataset_id}/report{suffix}",
        json={"format": "html", "include_forecast": True, "include_charts": True, "include_chat_summary": True},
        timeout=20,
    )
    if async_jobs:
        expect(response, 202, "report job")
        job = process_and_poll_job(session, base_url, response.json()["job_id"])
        payload = job.get("output") or {}
    else:
        expect(response, 200, "report")
        payload = response.json()
    if not payload.get("download_url"):
        raise SmokeFailure("report response missing download_url")
    print(f"PASS: report {payload.get('filename')}")
    return payload


def download_report(session: requests.Session, base_url: str, report: dict[str, Any]) -> None:
    response = session.get(f"{base_url}{report['download_url']}", timeout=20)
    expect(response, 200, "report download")
    if "Dataset Intelligence Report" not in response.text:
        raise SmokeFailure("downloaded report did not contain expected title")
    print("PASS: report download")


def create_and_download_backup(session: requests.Session, base_url: str) -> None:
    response = session.post(
        f"{base_url}/backups",
        json={"include_storage": True, "include_reports": True},
        timeout=45,
    )
    expect(response, 201, "backup")
    payload = response.json()
    backup_id = payload.get("backup_id")
    if not backup_id:
        raise SmokeFailure("backup response missing backup_id")
    list_response = session.get(f"{base_url}/backups", timeout=20)
    expect(list_response, 200, "backup list")
    download = session.get(f"{base_url}/backups/{backup_id}/download", timeout=45)
    expect(download, 200, "backup download")
    if not download.content.startswith(b"PK"):
        raise SmokeFailure("backup download is not a zip archive")
    print(f"PASS: backup {payload.get('filename')}")


def expect(response: requests.Response, status_code: int, label: str) -> None:
    if response.status_code != status_code:
        raise SmokeFailure(f"{label} returned {response.status_code}: {response.text[:300]}")


def process_and_poll_job(session: requests.Session, base_url: str, job_id: str) -> dict[str, Any]:
    try:
        from app.services.job_runner import run_next_job_once

        processed = None
        for _ in range(10):
            processed = run_next_job_once()
            response = session.get(f"{base_url}/jobs/{job_id}", timeout=10)
            expect(response, 200, f"job status {job_id}")
            payload = response.json()
            if payload.get("status") in {"succeeded", "failed", "cancelled"}:
                break
            if processed is None:
                raise SmokeFailure(f"no queued job was available for {job_id}")
    except ImportError as exc:
        raise SmokeFailure("async smoke requires running from the backend environment") from exc

    response = session.get(f"{base_url}/jobs/{job_id}", timeout=10)
    expect(response, 200, f"job status {job_id}")
    payload = response.json()
    if payload.get("status") != "succeeded":
        raise SmokeFailure(f"job {job_id} ended with status {payload.get('status')}: {payload.get('error_message')}")
    print(f"PASS: job {job_id} succeeded")
    return payload


if __name__ == "__main__":
    sys.exit(main())
