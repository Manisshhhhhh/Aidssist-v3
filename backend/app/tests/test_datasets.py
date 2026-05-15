from fastapi.testclient import TestClient

from app.core import paths


def upload_csv(client: TestClient):
    return client.post(
        "/upload",
        files={
            "file": (
                "sales.csv",
                b"date,sales,region\n2026-01-01,100,North\n2026-01-02,125,South\n",
                "text/csv",
            )
        },
    )


def test_get_datasets_returns_uploaded_dataset(client: TestClient) -> None:
    upload_response = upload_csv(client)
    dataset_id = upload_response.json()["dataset_id"]

    response = client.get("/datasets")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["dataset_id"] == dataset_id
    assert payload[0]["original_filename"] == "sales.csv"


def test_get_dataset_detail_returns_metadata(client: TestClient) -> None:
    upload_response = upload_csv(client)
    dataset_id = upload_response.json()["dataset_id"]

    response = client.get(f"/datasets/{dataset_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_id"] == dataset_id
    assert payload["row_count"] == 2
    assert payload["column_count"] == 3
    assert payload["columns"] == ["date", "sales", "region"]


def test_get_dataset_detail_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get("/datasets/unknown-dataset")

    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_delete_dataset_removes_dataset_folder(client: TestClient) -> None:
    upload_response = upload_csv(client)
    dataset_id = upload_response.json()["dataset_id"]
    dataset_dir = paths.DATASETS_DIR / dataset_id

    response = client.delete(f"/datasets/{dataset_id}")

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert not dataset_dir.exists()


def test_deleted_dataset_no_longer_appears_in_list(client: TestClient) -> None:
    upload_response = upload_csv(client)
    dataset_id = upload_response.json()["dataset_id"]

    client.delete(f"/datasets/{dataset_id}")
    response = client.get("/datasets")

    assert response.status_code == 200
    assert response.json() == []


def test_delete_dataset_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.delete("/datasets/unknown-dataset")

    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]
