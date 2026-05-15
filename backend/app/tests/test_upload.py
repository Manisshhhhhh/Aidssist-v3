import json
from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app.core import paths


def upload_csv(client: TestClient, filename: str = "sales.csv", content=None):
    csv_content = content or b"date,sales,region\n2026-01-01,100,North\n2026-01-02,125,South\n"
    return client.post(
        "/upload",
        files={"file": (filename, csv_content, "text/csv")},
    )


def test_upload_succeeds_with_valid_csv(client: TestClient) -> None:
    response = upload_csv(client)

    assert response.status_code == 201
    payload = response.json()
    assert payload["dataset_id"]
    assert payload["original_filename"] == "sales.csv"
    assert payload["stored_filename"] == "original.csv"
    assert payload["file_size_bytes"] > 0
    assert payload["row_count"] == 2
    assert payload["column_count"] == 3
    assert payload["columns"] == ["date", "sales", "region"]
    assert payload["created_at"]


def test_upload_rejects_non_csv_extension(client: TestClient) -> None:
    response = client.post(
        "/upload",
        files={"file": ("sales.txt", b"not,csv\n1,2\n", "text/plain")},
    )

    assert response.status_code == 400
    assert "Only CSV and Excel" in response.json()["detail"]


def test_upload_succeeds_with_excel_xlsx(client: TestClient) -> None:
    buffer = BytesIO()
    pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02"],
            "sales": [100, 125],
            "region": ["North", "South"],
        }
    ).to_excel(buffer, index=False)

    response = client.post(
        "/upload",
        files={
            "file": (
                "sales.xlsx",
                buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["original_filename"] == "sales.xlsx"
    assert payload["stored_filename"] == "original.csv"
    assert payload["row_count"] == 2
    assert payload["columns"] == ["date", "sales", "region"]

    original_path = Path(paths.DATASETS_DIR) / payload["dataset_id"] / "original.csv"
    assert original_path.read_text(encoding="utf-8").startswith("date,sales,region")


def test_upload_rejects_missing_file(client: TestClient) -> None:
    response = client.post("/upload")

    assert response.status_code == 400
    assert "required" in response.json()["detail"]


def test_upload_rejects_invalid_csv_content(client: TestClient) -> None:
    response = upload_csv(client, content=b"this is not a useful csv")

    assert response.status_code == 400
    assert "CSV" in response.json()["detail"]


def test_upload_rejects_file_larger_than_10mb(client: TestClient) -> None:
    content = b"a,b\n" + (b"1,2\n" * ((10 * 1024 * 1024 // 4) + 2))

    response = upload_csv(client, content=content)

    assert response.status_code == 400
    assert "10MB" in response.json()["detail"]


def test_upload_creates_original_csv(client: TestClient) -> None:
    response = upload_csv(client)
    dataset_id = response.json()["dataset_id"]

    original_path = Path(paths.DATASETS_DIR) / dataset_id / "original.csv"

    assert original_path.is_file()
    assert original_path.read_text(encoding="utf-8").startswith("date,sales,region")


def test_upload_creates_metadata_json(client: TestClient) -> None:
    response = upload_csv(client, filename="../unsafe sales.csv")
    dataset_id = response.json()["dataset_id"]
    metadata_path = Path(paths.DATASETS_DIR) / dataset_id / "metadata.json"

    assert metadata_path.is_file()
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["dataset_id"] == dataset_id
    assert metadata["original_filename"] == "unsafe_sales.csv"
    assert metadata["stored_filename"] == "original.csv"
