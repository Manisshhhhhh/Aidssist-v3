from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.core import paths


def upload_csv(client: TestClient, csv_content: bytes, filename: str = "forecast.csv") -> str:
    response = client.post(
        "/upload",
        files={"file": (filename, csv_content, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["dataset_id"]


def post_forecast(
    client: TestClient,
    dataset_id: str,
    date_column: str = "date",
    target_column: str = "sales",
    periods: int = 3,
    frequency: str = "auto",
    model: str = "auto",
):
    return client.post(
        f"/datasets/{dataset_id}/forecast",
        json={
            "date_column": date_column,
            "target_column": target_column,
            "periods": periods,
            "frequency": frequency,
            "model": model,
        },
    )


def daily_series_csv(points: int = 12) -> bytes:
    rows = ["date,sales"]
    for index in range(points):
        rows.append(f"2026-01-{index + 1:02d},{100 + index * 10}")
    return "\n".join(rows).encode("utf-8")


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


def test_forecast_succeeds_for_valid_daily_time_series(client: TestClient) -> None:
    dataset_id = upload_csv(client, daily_series_csv())

    response = post_forecast(client, dataset_id, periods=5)

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_id"] == dataset_id
    assert payload["date_column"] == "date"
    assert payload["target_column"] == "sales"
    assert payload["frequency"] == "D"
    assert len(payload["historical_points"]) == 12
    assert len(payload["forecast_points"]) == 5
    assert payload["assumptions"]
    assert payload["warnings"]


def test_unknown_dataset_returns_404(client: TestClient) -> None:
    response = post_forecast(client, "unknown-dataset")

    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_missing_date_column_returns_400(client: TestClient) -> None:
    dataset_id = upload_csv(client, daily_series_csv())

    response = post_forecast(client, dataset_id, date_column="missing_date")

    assert response.status_code == 400
    assert "Date column" in response.json()["detail"]


def test_missing_target_column_returns_400(client: TestClient) -> None:
    dataset_id = upload_csv(client, daily_series_csv())

    response = post_forecast(client, dataset_id, target_column="missing_sales")

    assert response.status_code == 400
    assert "Target column" in response.json()["detail"]


def test_non_parseable_date_column_returns_400(client: TestClient) -> None:
    dataset_id = upload_csv(
        client,
        b"date,sales\nalpha,10\nbravo,20\ncharlie,30\ndelta,40\necho,50\n",
    )

    response = post_forecast(client, dataset_id)

    assert response.status_code == 400
    assert "not parseable" in response.json()["detail"]


def test_non_numeric_target_column_returns_400(client: TestClient) -> None:
    dataset_id = upload_csv(
        client,
        b"date,sales\n2026-01-01,high\n2026-01-02,low\n2026-01-03,medium\n2026-01-04,high\n2026-01-05,low\n",
    )

    response = post_forecast(client, dataset_id)

    assert response.status_code == 400
    assert "not numeric" in response.json()["detail"]


def test_fewer_than_5_valid_points_returns_400(client: TestClient) -> None:
    dataset_id = upload_csv(
        client,
        b"date,sales\n2026-01-01,10\n2026-01-02,20\n2026-01-03,30\n2026-01-04,40\n2026-01-05,\n",
    )

    response = post_forecast(client, dataset_id)

    assert response.status_code == 400
    assert "At least 5 valid time points" in response.json()["detail"]


def test_duplicate_dates_are_aggregated_and_warning_is_returned(client: TestClient) -> None:
    dataset_id = upload_csv(
        client,
        b"date,sales\n"
        b"2026-01-01,10\n2026-01-01,20\n2026-01-02,30\n2026-01-03,40\n"
        b"2026-01-04,50\n2026-01-05,60\n",
    )

    response = post_forecast(client, dataset_id)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["historical_points"]) == 5
    assert any("Duplicate dates" in warning for warning in payload["warnings"])
    assert any("aggregated using the mean" in assumption for assumption in payload["assumptions"])


def test_missing_rows_are_dropped_and_warning_is_returned(client: TestClient) -> None:
    dataset_id = upload_csv(
        client,
        b"date,sales\n"
        b"2026-01-01,10\n2026-01-02,20\n2026-01-03,\n2026-01-04,40\n"
        b"2026-01-05,50\n2026-01-06,60\n",
    )

    response = post_forecast(client, dataset_id)

    assert response.status_code == 200
    assert any("rows were dropped" in warning for warning in response.json()["warnings"])


def test_auto_model_uses_linear_regression_when_enough_points_exist(client: TestClient) -> None:
    dataset_id = upload_csv(client, daily_series_csv(12))

    response = post_forecast(client, dataset_id)

    assert response.status_code == 200
    assert response.json()["model_used"] == "linear_regression"


def test_auto_model_uses_moving_average_for_small_valid_datasets(client: TestClient) -> None:
    dataset_id = upload_csv(client, daily_series_csv(7))

    response = post_forecast(client, dataset_id)

    assert response.status_code == 200
    assert response.json()["model_used"] == "moving_average"


def test_forecast_response_contains_requested_number_of_forecast_points(client: TestClient) -> None:
    dataset_id = upload_csv(client, daily_series_csv(12))

    response = post_forecast(client, dataset_id, periods=8)

    assert response.status_code == 200
    assert len(response.json()["forecast_points"]) == 8


def test_forecast_json_file_is_saved(client: TestClient) -> None:
    dataset_id = upload_csv(client, daily_series_csv(12))

    response = post_forecast(client, dataset_id)

    assert response.status_code == 200
    forecast_path = Path(paths.DATASETS_DIR) / dataset_id / "forecast_date_sales.json"
    assert forecast_path.is_file()
    saved_forecast = json.loads(forecast_path.read_text(encoding="utf-8"))
    assert saved_forecast["dataset_id"] == dataset_id


def test_forecast_response_is_json_safe_without_nan(client: TestClient) -> None:
    dataset_id = upload_csv(client, daily_series_csv(12))

    response = post_forecast(client, dataset_id)

    assert response.status_code == 200
    payload = response.json()
    json.dumps(payload)
    assert_no_nan(payload)


def test_metrics_are_returned_when_enough_points_exist(client: TestClient) -> None:
    dataset_id = upload_csv(client, daily_series_csv(12))

    response = post_forecast(client, dataset_id)

    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert metrics["mae"] is not None
    assert metrics["rmse"] is not None
    assert metrics["mape"] is not None


def test_non_negative_history_does_not_produce_negative_lower_bounds(client: TestClient) -> None:
    dataset_id = upload_csv(
        client,
        b"date,sales\n"
        b"2026-01-01,0\n2026-01-02,0\n2026-01-03,0\n2026-01-04,0\n2026-01-05,0\n"
        b"2026-01-06,0\n2026-01-07,0\n2026-01-08,0\n2026-01-09,0\n2026-01-10,100\n",
    )

    response = post_forecast(client, dataset_id, periods=4)

    assert response.status_code == 200
    assert all(point["lower_bound"] >= 0 for point in response.json()["forecast_points"])
