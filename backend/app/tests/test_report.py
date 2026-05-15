from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.core import paths


def upload_csv(client: TestClient, content: bytes, filename: str = "report.csv") -> str:
    response = client.post("/upload", files={"file": (filename, content, "text/csv")})
    assert response.status_code == 201
    return response.json()["dataset_id"]


def analyze(client: TestClient, dataset_id: str) -> dict[str, Any]:
    response = client.post(f"/datasets/{dataset_id}/analyze")
    assert response.status_code == 200
    return response.json()


def create_report(client: TestClient, dataset_id: str, payload: dict[str, Any]) -> Any:
    return client.post(f"/datasets/{dataset_id}/report", json=payload)


def assert_no_nan(value: Any) -> None:
    if isinstance(value, dict):
        for nested_value in value.values():
            assert_no_nan(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            assert_no_nan(nested_value)
    elif isinstance(value, float):
        assert not math.isnan(value)
        assert not math.isinf(value)


def test_unknown_dataset_returns_404(client: TestClient) -> None:
    response = create_report(client, "unknown", {"format": "html"})

    assert response.status_code == 404


def test_path_like_dataset_id_returns_404(client: TestClient) -> None:
    response = create_report(client, "..%2Foutside", {"format": "html"})

    assert response.status_code == 404


def test_report_generation_returns_400_if_analysis_has_not_been_run(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,sales\n2026-01-01,10\n")

    response = create_report(client, dataset_id, {"format": "html"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Run analysis before generating a report."


def test_html_report_generation_succeeds_after_analysis(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,region,sales\n2026-01-01,North,10\n2026-01-02,South,20\n")
    analyze(client, dataset_id)

    response = create_report(client, dataset_id, {"format": "html"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["format"] == "html"
    assert payload["filename"].endswith(".html")
    assert payload["download_url"].endswith(f"/reports/{payload['report_id']}/download")


def test_json_report_generation_succeeds_after_analysis(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,region,sales\n2026-01-01,North,10\n2026-01-02,South,20\n")
    analyze(client, dataset_id)

    response = create_report(client, dataset_id, {"format": "json"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["format"] == "json"
    assert payload["filename"].endswith(".json")


def test_report_files_are_saved_under_dataset_reports_folder(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,sales\n2026-01-01,10\n2026-01-02,20\n")
    analyze(client, dataset_id)

    payload = create_report(client, dataset_id, {"format": "html"}).json()
    report_dir = Path(paths.DATASETS_DIR) / dataset_id / "reports" / payload["report_id"]

    assert (report_dir / "report.html").is_file()
    assert (report_dir / "report.json").is_file()
    assert (report_dir / "manifest.json").is_file()


def test_download_endpoint_returns_generated_html_report(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,sales\n2026-01-01,10\n2026-01-02,20\n")
    analyze(client, dataset_id)
    payload = create_report(client, dataset_id, {"format": "html"}).json()

    response = client.get(payload["download_url"])

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Dataset Intelligence Report" in response.text


def test_download_endpoint_returns_generated_json_report(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,sales\n2026-01-01,10\n2026-01-02,20\n")
    analyze(client, dataset_id)
    payload = create_report(client, dataset_id, {"format": "json"}).json()

    response = client.get(payload["download_url"])

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["dataset"]["dataset_id"] == dataset_id


def test_report_includes_dataset_overview(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,sales\n2026-01-01,10\n2026-01-02,20\n")
    analyze(client, dataset_id)
    payload = create_report(client, dataset_id, {"format": "json"}).json()

    report = client.get(payload["download_url"]).json()

    assert report["dataset"]["row_count"] == 2
    assert report["dataset"]["column_count"] == 2
    assert report["dataset"]["columns"] == ["date", "sales"]


def test_report_includes_quality_and_insights(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,region,sales\n2026-01-01,,10\n2026-01-01,,10\n")
    analyze(client, dataset_id)
    payload = create_report(client, dataset_id, {"format": "json"}).json()

    report = client.get(payload["download_url"]).json()

    assert report["analysis"]["quality"]["missing_cells"] == 2
    assert report["analysis"]["quality"]["duplicate_rows"] == 1
    assert report["analysis"]["insights"]


def test_report_includes_forecast_summary_if_forecast_exists(client: TestClient) -> None:
    csv = "date,sales\n" + "\n".join(f"2026-01-{day:02d},{day * 10}" for day in range(1, 11)) + "\n"
    dataset_id = upload_csv(client, csv.encode())
    analyze(client, dataset_id)
    forecast_response = client.post(
        f"/datasets/{dataset_id}/forecast",
        json={"date_column": "date", "target_column": "sales", "periods": 3, "frequency": "D", "model": "auto"},
    )
    assert forecast_response.status_code == 200

    payload = create_report(client, dataset_id, {"format": "json", "include_forecast": True}).json()
    report = client.get(payload["download_url"]).json()

    assert report["forecast"]["target_column"] == "sales"
    assert report["forecast"]["forecast_points"]


def test_report_handles_missing_forecast_cleanly(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,sales\n2026-01-01,10\n2026-01-02,20\n")
    analyze(client, dataset_id)
    payload = create_report(client, dataset_id, {"format": "html", "include_forecast": True}).json()

    response = client.get(payload["download_url"])

    assert "No forecast has been generated for this dataset." in response.text


def test_unsupported_format_returns_validation_error(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,sales\n2026-01-01,10\n2026-01-02,20\n")
    analyze(client, dataset_id)

    response = create_report(client, dataset_id, {"format": "pdf"})

    assert response.status_code == 422


def test_html_escapes_unsafe_dataset_content(client: TestClient) -> None:
    dataset_id = upload_csv(
        client,
        b"<script>alert(1)</script>,sales\nunsafe,10\n",
        filename="<script>alert(1)</script>.csv",
    )
    analyze(client, dataset_id)
    payload = create_report(client, dataset_id, {"format": "html"}).json()

    response = client.get(payload["download_url"])

    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text


def test_report_output_is_json_safe_without_nan(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"category,value\nA,1\nB,\nC,3\n")
    analyze(client, dataset_id)
    payload = create_report(client, dataset_id, {"format": "json"}).json()

    report = json.loads(client.get(payload["download_url"]).text)

    assert_no_nan(report)
