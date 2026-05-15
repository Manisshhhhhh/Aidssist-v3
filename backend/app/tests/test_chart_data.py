from __future__ import annotations

import math
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.core import paths


def upload_csv(client: TestClient, content: bytes, filename: str = "charts.csv") -> str:
    response = client.post("/upload", files={"file": (filename, content, "text/csv")})
    assert response.status_code == 201
    return response.json()["dataset_id"]


def analyze(client: TestClient, dataset_id: str) -> dict[str, Any]:
    response = client.post(f"/datasets/{dataset_id}/analyze")
    assert response.status_code == 200
    return response.json()


def get_chart(client: TestClient, dataset_id: str, chart_id: str):
    return client.get(f"/datasets/{dataset_id}/charts/{chart_id}/data")


def get_chart_with_range(client: TestClient, dataset_id: str, chart_id: str, time_range: str):
    return client.get(f"/datasets/{dataset_id}/charts/{chart_id}/data?time_range={time_range}")


def chart_id_for(analysis: dict[str, Any], chart_type: str, x: str | None = None, y: str | None = None) -> str:
    for chart in analysis["recommended_charts"]:
        if chart["chart_type"] != chart_type:
            continue
        if x is not None and chart["x"] != x:
            continue
        if y is not None and chart["y"] != y:
            continue
        return chart["chart_id"]
    raise AssertionError(f"Missing chart {chart_type} {x} {y}")


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


def test_chart_data_returns_400_if_analysis_has_not_been_run(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,sales\n2026-01-01,10\n2026-01-02,20\n")

    response = get_chart(client, dataset_id, "date_sales_line")

    assert response.status_code == 400
    assert response.json()["detail"] == "Run analysis before requesting chart data."


def test_unknown_dataset_returns_404(client: TestClient) -> None:
    response = get_chart(client, "unknown-dataset", "missing")

    assert response.status_code == 404


def test_unknown_chart_id_returns_404(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,sales\n2026-01-01,10\n2026-01-02,20\n")
    analyze(client, dataset_id)

    response = get_chart(client, dataset_id, "unknown-chart")

    assert response.status_code == 404


def test_line_chart_data_is_generated_for_datetime_numeric(client: TestClient) -> None:
    dataset_id = upload_csv(
        client,
        b"date,sales\n2026-01-01,10\n2026-01-01,20\n2026-01-02,30\n",
    )
    analysis = analyze(client, dataset_id)

    response = get_chart(client, dataset_id, chart_id_for(analysis, "line", "date", "sales"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["chart_type"] == "line"
    assert payload["metadata"]["aggregation"] == "sum"
    assert payload["data"][0]["y"] == 30
    assert payload["data"][0]["x"].startswith("2026-01-01")


def test_line_chart_data_supports_time_range_filter(client: TestClient) -> None:
    rows = ["date,sales"]
    start = date(2026, 1, 1)
    for day in range(40):
        rows.append(f"{(start + timedelta(days=day)).isoformat()},{day + 1}")
    dataset_id = upload_csv(client, ("\n".join(rows) + "\n").encode())
    analysis = analyze(client, dataset_id)

    response = get_chart_with_range(client, dataset_id, chart_id_for(analysis, "line", "date", "sales"), "1w")

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["time_range"] == "1w"
    assert len(payload["data"]) < 40


def test_chart_data_rejects_unsupported_time_range(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"date,sales\n2026-01-01,10\n2026-01-02,20\n")
    analysis = analyze(client, dataset_id)

    response = get_chart_with_range(client, dataset_id, chart_id_for(analysis, "line", "date", "sales"), "10y")

    assert response.status_code == 400
    assert "Unsupported time range" in response.json()["detail"]


def test_bar_chart_data_is_generated_for_categorical_numeric(client: TestClient) -> None:
    dataset_id = upload_csv(
        client,
        b"region,sales\nNorth,10\nNorth,30\nSouth,15\n",
    )
    analysis = analyze(client, dataset_id)

    response = get_chart(client, dataset_id, chart_id_for(analysis, "bar", "region", "sales"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["chart_type"] == "bar"
    assert payload["data"][0]["x"] == "North"
    assert payload["data"][0]["y"] == 40


def test_categorical_frequency_bar_chart_works(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"region\nNorth\nNorth\nSouth\n")
    analysis = analyze(client, dataset_id)

    response = get_chart(client, dataset_id, chart_id_for(analysis, "bar", "region"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["aggregation"] == "count"
    assert payload["data"][0] == {"x": "North", "y": 2, "label": "North"}


def test_pie_chart_groups_extra_categories_into_other(client: TestClient) -> None:
    content = "region\nA\nB\nC\nD\nE\nF\nG\nH\n".encode("utf-8")
    dataset_id = upload_csv(client, content)
    analyze(client, dataset_id)
    analysis_path = Path(paths.DATASETS_DIR) / dataset_id / "analysis.json"
    analysis_payload = json.loads(analysis_path.read_text(encoding="utf-8"))
    analysis_payload["recommended_charts"].append(
        {
            "chart_id": "region_pie_manual",
            "title": "Region share",
            "description": "Shows region share.",
            "chart_type": "pie",
            "x": "region",
            "y": None,
            "series": None,
            "priority": 50,
            "reason": "Manual test chart.",
            "config": {"aggregation": "count", "limit": 6},
        }
    )
    analysis_path.write_text(json.dumps(analysis_payload), encoding="utf-8")

    response = get_chart(client, dataset_id, "region_pie_manual")

    assert response.status_code == 200
    labels = [item["label"] for item in response.json()["data"]]
    assert "Other" in labels


def test_histogram_chart_data_works(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"sales\n10\n20\n30\n40\n50\n60\n")
    analysis = analyze(client, dataset_id)

    response = get_chart(client, dataset_id, chart_id_for(analysis, "histogram", "sales"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["chart_type"] == "histogram"
    assert {"x", "y", "bin_start", "bin_end", "label"}.issubset(payload["data"][0])


def test_scatter_chart_data_works(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"sales,profit\n1,2\n2,4\n3,6\n4,8\n")
    analysis = analyze(client, dataset_id)

    response = get_chart(client, dataset_id, chart_id_for(analysis, "scatter", "sales", "profit"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["chart_type"] == "scatter"
    assert payload["data"][0]["x"] == 1
    assert payload["data"][0]["y"] == 2


def test_heatmap_chart_data_works(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"a,b,c\n1,2,3\n2,4,5\n3,6,7\n4,8,9\n")
    analysis = analyze(client, dataset_id)

    response = get_chart(client, dataset_id, chart_id_for(analysis, "heatmap"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["chart_type"] == "heatmap"
    assert len(payload["data"]) == 9
    assert {"x", "y", "value", "label"}.issubset(payload["data"][0])


def test_box_chart_data_works(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"value\n1\n2\n2\n3\n4\n100\n")
    analysis = analyze(client, dataset_id)

    response = get_chart(client, dataset_id, chart_id_for(analysis, "box", "value"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["chart_type"] == "box"
    assert payload["data"][0]["x"] == "value"
    assert payload["data"][0]["outlier_count"] == 1


def test_chart_data_output_is_json_safe_without_nan(client: TestClient) -> None:
    dataset_id = upload_csv(client, b"sales,profit\n1,2\n2,4\n3,6\n4,8\n")
    analysis = analyze(client, dataset_id)

    response = get_chart(client, dataset_id, chart_id_for(analysis, "scatter", "sales", "profit"))

    assert response.status_code == 200
    assert_no_nan(response.json())


def test_chart_data_row_limits_are_respected(client: TestClient) -> None:
    start = date(2026, 1, 1)
    rows = ["date,sales"]
    for index in range(620):
        rows.append(f"{(start + timedelta(days=index)).isoformat()},{index}")
    dataset_id = upload_csv(client, "\n".join(rows).encode("utf-8"))
    analysis = analyze(client, dataset_id)

    response = get_chart(client, dataset_id, chart_id_for(analysis, "line", "date", "sales"))

    assert response.status_code == 200
    assert len(response.json()["data"]) == 500
