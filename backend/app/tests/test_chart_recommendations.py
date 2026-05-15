from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def analyze_csv(client: TestClient, csv_content: bytes, filename: str = "charts.csv") -> dict[str, Any]:
    upload_response = client.post(
        "/upload",
        files={"file": (filename, csv_content, "text/csv")},
    )
    assert upload_response.status_code == 201
    dataset_id = upload_response.json()["dataset_id"]

    analysis_response = client.post(f"/datasets/{dataset_id}/analyze")
    assert analysis_response.status_code == 200
    return analysis_response.json()


def chart_exists(charts: list[dict[str, Any]], chart_type: str, x: str | None = None, y: str | None = None) -> bool:
    for chart in charts:
        if chart["chart_type"] != chart_type:
            continue
        if x is not None and chart["x"] != x:
            continue
        if y is not None and chart["y"] != y:
            continue
        return True
    return False


def test_datetime_numeric_dataset_recommends_line_chart(client: TestClient) -> None:
    analysis = analyze_csv(
        client,
        b"date,sales\n2026-01-01,10\n2026-01-02,20\n2026-01-03,30\n",
    )

    assert chart_exists(analysis["recommended_charts"], "line", "date", "sales")


def test_categorical_numeric_dataset_recommends_bar_chart(client: TestClient) -> None:
    analysis = analyze_csv(
        client,
        b"region,sales\nNorth,10\nSouth,20\nNorth,30\n",
    )

    assert chart_exists(analysis["recommended_charts"], "bar", "region", "sales")


def test_correlated_numeric_dataset_recommends_scatter_chart(client: TestClient) -> None:
    analysis = analyze_csv(
        client,
        b"x,y\n1,2\n2,4\n3,6\n4,8\n",
    )

    assert chart_exists(analysis["recommended_charts"], "scatter", "x", "y")


def test_three_numeric_columns_recommend_heatmap(client: TestClient) -> None:
    analysis = analyze_csv(
        client,
        b"a,b,c\n1,2,3\n2,4,5\n3,6,7\n4,8,9\n",
    )

    assert chart_exists(analysis["recommended_charts"], "heatmap")


def test_low_cardinality_categorical_column_recommends_pie_chart(client: TestClient) -> None:
    analysis = analyze_csv(
        client,
        b"region\nNorth\nSouth\nNorth\nEast\n",
    )

    assert chart_exists(analysis["recommended_charts"], "pie", "region")


def test_high_cardinality_categorical_column_does_not_recommend_pie_chart(client: TestClient) -> None:
    rows = ["category"] + [f"category_{index}" for index in range(31)]
    analysis = analyze_csv(client, "\n".join(rows).encode("utf-8"))

    assert not any(chart["chart_type"] == "pie" for chart in analysis["recommended_charts"])


def test_recommended_charts_are_sorted_by_priority_descending(client: TestClient) -> None:
    analysis = analyze_csv(
        client,
        b"date,region,sales,profit,units\n"
        b"2026-01-01,North,10,2,1\n"
        b"2026-01-02,South,20,4,2\n"
        b"2026-01-03,North,30,6,3\n"
        b"2026-01-04,East,40,8,4\n",
    )
    priorities = [chart["priority"] for chart in analysis["recommended_charts"]]

    assert priorities == sorted(priorities, reverse=True)


def test_recommended_charts_length_is_max_20(client: TestClient) -> None:
    headers = ["date"] + [f"metric_{index}" for index in range(8)] + [f"category_{index}" for index in range(8)]
    rows = [",".join(headers)]
    for row_index in range(35):
        row = [f"2026-01-{(row_index % 28) + 1:02d}"]
        row.extend(str(row_index + metric_index) for metric_index in range(8))
        row.extend(f"group_{(row_index + category_index) % 4}" for category_index in range(8))
        rows.append(",".join(row))

    analysis = analyze_csv(client, "\n".join(rows).encode("utf-8"))

    assert len(analysis["recommended_charts"]) <= 20
