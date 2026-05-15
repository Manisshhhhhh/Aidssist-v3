from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2, "info": 3}


def analyze_csv(client: TestClient, csv_content: bytes, filename: str = "insights.csv") -> dict[str, Any]:
    upload_response = client.post(
        "/upload",
        files={"file": (filename, csv_content, "text/csv")},
    )
    assert upload_response.status_code == 201
    dataset_id = upload_response.json()["dataset_id"]

    analysis_response = client.post(f"/datasets/{dataset_id}/analyze")
    assert analysis_response.status_code == 200
    return analysis_response.json()


def has_insight(analysis: dict[str, Any], insight_type: str, title_contains: str | None = None) -> bool:
    for insight in analysis["insights"]:
        if insight["type"] != insight_type:
            continue
        if title_contains is not None and title_contains not in insight["title"]:
            continue
        return True
    return False


def test_missing_values_produce_missing_value_insight(client: TestClient) -> None:
    analysis = analyze_csv(client, b"region,sales\nNorth,10\n,20\n")

    assert has_insight(analysis, "missing_values")


def test_duplicate_rows_produce_duplicate_row_insight(client: TestClient) -> None:
    analysis = analyze_csv(client, b"region,sales\nNorth,10\nNorth,10\nSouth,20\n")

    assert has_insight(analysis, "duplicates")


def test_constant_column_produces_constant_column_insight(client: TestClient) -> None:
    analysis = analyze_csv(client, b"region,constant\nNorth,A\nSouth,A\nEast,A\n")

    assert has_insight(analysis, "constant_columns")


def test_strong_positive_correlation_produces_correlation_insight(client: TestClient) -> None:
    analysis = analyze_csv(client, b"sales,profit\n1,2\n2,4\n3,6\n4,8\n")

    assert has_insight(analysis, "correlation", "Strong positive")


def test_strong_negative_correlation_produces_correlation_insight(client: TestClient) -> None:
    analysis = analyze_csv(client, b"x,y\n1,8\n2,6\n3,4\n4,2\n")

    assert has_insight(analysis, "correlation", "Strong negative")


def test_skewed_numeric_column_produces_skew_insight(client: TestClient) -> None:
    analysis = analyze_csv(client, b"value\n1\n1\n1\n1\n100\n")

    assert has_insight(analysis, "skew")


def test_outliers_produce_outlier_insight(client: TestClient) -> None:
    analysis = analyze_csv(client, b"value\n1\n2\n2\n3\n4\n100\n")

    assert has_insight(analysis, "outliers")


def test_low_quality_score_produces_quality_insight(client: TestClient) -> None:
    rows = ["value,empty,constant"] + ["1,,A" for _ in range(40)]
    analysis = analyze_csv(client, "\n".join(rows).encode("utf-8"))

    assert analysis["quality"]["quality_score"] < 70
    assert has_insight(analysis, "data_quality", "Low")


def test_small_dataset_produces_small_dataset_warning(client: TestClient) -> None:
    analysis = analyze_csv(client, b"region,sales\nNorth,10\nSouth,20\n")

    assert has_insight(analysis, "dataset_size", "Small")


def test_insights_are_sorted_by_severity(client: TestClient) -> None:
    analysis = analyze_csv(
        client,
        b"date,sales,profit,region,constant\n"
        b"2026-01-01,1,10,North,A\n"
        b"2026-01-02,2,8,,A\n"
        b"2026-01-03,3,6,,A\n"
        b"2026-01-04,4,4,South,A\n",
    )
    ranks = [SEVERITY_RANK[insight["severity"]] for insight in analysis["insights"]]

    assert ranks == sorted(ranks)
