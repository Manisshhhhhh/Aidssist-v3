import json
import math
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.core import paths


MIXED_CSV = (
    b"date,sales,profit,region,active,notes,constant\n"
    b"2026-01-01,100,20,North,yes,short,A\n"
    b"2026-01-02,200,40,South,no,medium,A\n"
    b"2026-01-03,300,60,,yes,longer,A\n"
    b"2026-01-03,300,60,,yes,longer,A\n"
    b"2026-01-04,400,80,East,no,another,A\n"
)


def upload_mixed_csv(client: TestClient) -> str:
    response = client.post(
        "/upload",
        files={"file": ("mixed.csv", MIXED_CSV, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["dataset_id"]


def analyze_uploaded_dataset(client: TestClient) -> dict[str, Any]:
    dataset_id = upload_mixed_csv(client)
    response = client.post(f"/datasets/{dataset_id}/analyze")
    assert response.status_code == 200
    return response.json()


def column_by_name(analysis: dict[str, Any], name: str) -> dict[str, Any]:
    return next(column for column in analysis["columns"] if column["name"] == name)


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


def test_analyze_succeeds_for_valid_mixed_csv(client: TestClient) -> None:
    analysis = analyze_uploaded_dataset(client)

    assert analysis["dataset_id"]
    assert analysis["created_at"]
    assert len(analysis["columns"]) == 7


def test_analyze_creates_analysis_json(client: TestClient) -> None:
    dataset_id = upload_mixed_csv(client)

    response = client.post(f"/datasets/{dataset_id}/analyze")

    assert response.status_code == 200
    analysis_path = Path(paths.DATASETS_DIR) / dataset_id / "analysis.json"
    assert analysis_path.is_file()
    saved_analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    assert saved_analysis["dataset_id"] == dataset_id


def test_analyze_response_has_counts(client: TestClient) -> None:
    analysis = analyze_uploaded_dataset(client)

    assert analysis["row_count"] == 5
    assert analysis["column_count"] == 7


def test_numeric_column_has_numeric_stats(client: TestClient) -> None:
    analysis = analyze_uploaded_dataset(client)
    sales = column_by_name(analysis, "sales")

    assert sales["semantic_type"] == "numeric"
    assert sales["stats"]["mean"] == 260.0
    assert sales["stats"]["median"] == 300.0
    assert sales["stats"]["min"] == 100
    assert sales["stats"]["max"] == 400
    assert sales["stats"]["q1"] == 200.0
    assert sales["stats"]["q3"] == 300.0


def test_categorical_column_has_top_values(client: TestClient) -> None:
    analysis = analyze_uploaded_dataset(client)
    region = column_by_name(analysis, "region")

    assert region["semantic_type"] == "categorical"
    assert "top_values" in region["stats"]
    assert region["stats"]["top_values"][0]["value"] in {"North", "South", "East"}


def test_datetime_column_is_detected(client: TestClient) -> None:
    analysis = analyze_uploaded_dataset(client)
    date = column_by_name(analysis, "date")

    assert date["semantic_type"] == "datetime"
    assert date["stats"]["min_date"].startswith("2026-01-01")
    assert date["stats"]["max_date"].startswith("2026-01-04")
    assert date["stats"]["range_days"] == 3


def test_duplicate_rows_are_counted(client: TestClient) -> None:
    analysis = analyze_uploaded_dataset(client)

    assert analysis["quality"]["duplicate_rows"] == 1
    assert analysis["quality"]["duplicate_percent"] == 20.0


def test_missing_values_are_counted(client: TestClient) -> None:
    analysis = analyze_uploaded_dataset(client)
    region = column_by_name(analysis, "region")

    assert analysis["quality"]["missing_cells"] == 2
    assert region["missing_count"] == 2
    assert region["missing_percent"] == 40.0


def test_correlations_are_returned_for_correlated_numeric_columns(client: TestClient) -> None:
    analysis = analyze_uploaded_dataset(client)

    assert analysis["correlations"]
    first_correlation = analysis["correlations"][0]
    assert {first_correlation["column_a"], first_correlation["column_b"]} == {"sales", "profit"}
    assert first_correlation["correlation"] == 1.0


def test_unknown_dataset_returns_404(client: TestClient) -> None:
    response = client.post("/datasets/unknown-dataset/analyze")

    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_unreadable_stored_csv_returns_400(client: TestClient) -> None:
    dataset_id = upload_mixed_csv(client)
    original_path = Path(paths.DATASETS_DIR) / dataset_id / "original.csv"
    original_path.write_text('"unterminated\n1,2', encoding="utf-8")

    response = client.post(f"/datasets/{dataset_id}/analyze")

    assert response.status_code == 400
    assert "could not be read" in response.json()["detail"]


def test_analysis_output_is_json_safe_without_nan(client: TestClient) -> None:
    analysis = analyze_uploaded_dataset(client)

    json.dumps(analysis)
    assert_no_nan(analysis)


def test_analysis_response_includes_recommended_charts_and_insights(client: TestClient) -> None:
    analysis = analyze_uploaded_dataset(client)

    assert "recommended_charts" in analysis
    assert isinstance(analysis["recommended_charts"], list)
    assert analysis["recommended_charts"]
    assert "insights" in analysis
    assert isinstance(analysis["insights"], list)
    assert analysis["insights"]


def test_quality_score_includes_issue_breakdown(client: TestClient) -> None:
    rows = ["date,value,category"]
    for index in range(1, 26):
        date = "not-a-date" if index == 13 else f"2026-01-{index:02d}"
        value = 1000 if index == 25 else index
        rows.append(f"{date},{value},category-{index}")
    response = client.post(
        "/upload",
        files={"file": ("quality.csv", "\n".join(rows).encode("utf-8"), "text/csv")},
    )
    dataset_id = response.json()["dataset_id"]

    analysis_response = client.post(f"/datasets/{dataset_id}/analyze")

    assert analysis_response.status_code == 200
    quality = analysis_response.json()["quality"]
    issue_types = {issue["type"] for issue in quality["issue_breakdown"]}
    assert quality["quality_score"] < 100
    assert "date" in quality["date_parse_issue_columns"]
    assert "category" in quality["high_cardinality_columns"]
    assert "value" in quality["outlier_columns"]
    assert {"date_parse_issues", "high_cardinality", "outliers"}.issubset(issue_types)
