import json
import math
from typing import Any

from fastapi.testclient import TestClient


CHAT_CSV = (
    b"date,sales,profit,region,product\n"
    b"2026-01-01,100,20,North,A\n"
    b"2026-01-02,120,24,South,B\n"
    b"2026-01-03,140,28,North,A\n"
    b"2026-01-04,160,32,South,B\n"
    b"2026-01-04,160,32,South,B\n"
    b"2026-01-05,,35,East,C\n"
)


def upload_chat_csv(client: TestClient, content: bytes = CHAT_CSV, filename: str = "chat.csv") -> str:
    response = client.post("/upload", files={"file": (filename, content, "text/csv")})
    assert response.status_code == 201
    return response.json()["dataset_id"]


def ask(client: TestClient, dataset_id: str, message: str) -> dict[str, Any]:
    response = client.post(f"/datasets/{dataset_id}/chat", json={"message": message})
    assert response.status_code == 200
    return response.json()


def analyze(client: TestClient, dataset_id: str) -> None:
    response = client.post(f"/datasets/{dataset_id}/analyze")
    assert response.status_code == 200


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


def test_unknown_dataset_id_returns_404(client: TestClient) -> None:
    response = client.post("/datasets/unknown/chat", json={"message": "summarize this dataset"})

    assert response.status_code == 404


def test_basic_summary_question_works_without_analysis(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)

    response = ask(client, dataset_id, "summarize this dataset")

    assert response["intent"] == "dataset_summary"
    assert "6 rows" in response["answer"]


def test_column_list_works(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)

    response = ask(client, dataset_id, "what columns are available?")

    assert response["intent"] == "column_list"
    assert "sales" in response["answer"]


def test_missing_values_question_works_after_analysis(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)
    analyze(client, dataset_id)

    response = ask(client, dataset_id, "which columns have missing values?")

    assert response["intent"] == "missing_values"
    assert response["result"]["type"] == "table"
    assert response["result"]["data"][0]["column"] == "sales"


def test_duplicate_question_works_after_analysis(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)
    analyze(client, dataset_id)

    response = ask(client, dataset_id, "are there duplicate rows?")

    assert response["intent"] == "duplicates"
    assert response["result"]["data"]["value"] == 1


def test_numeric_average_question_works(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)

    response = ask(client, dataset_id, "average sales")

    assert response["intent"] == "numeric_summary"
    assert response["result"]["data"]["value"] == 136.0


def test_total_sum_question_works(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)

    response = ask(client, dataset_id, "total profit")

    assert response["intent"] == "numeric_summary"
    assert response["result"]["data"]["value"] == 171.0


def test_groupby_aggregate_works(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)

    response = ask(client, dataset_id, "average sales by region")

    assert response["intent"] == "groupby_aggregate"
    assert response["result"]["type"] == "table"
    assert response["columns_used"] == ["sales", "region"]


def test_top_n_rows_respects_max_20(client: TestClient) -> None:
    rows = ["id,sales"]
    rows.extend(f"{index},{index}" for index in range(40))
    dataset_id = upload_chat_csv(client, "\n".join(rows).encode("utf-8"), "top.csv")

    response = ask(client, dataset_id, "top 30 rows by sales")

    assert response["intent"] == "top_bottom_records"
    assert len(response["result"]["data"]) == 20


def test_correlation_lookup_works_after_analysis(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)
    analyze(client, dataset_id)

    response = ask(client, dataset_id, "correlation between sales and profit")

    assert response["intent"] == "correlation_lookup"
    assert response["result"]["data"]


def test_chart_recommendation_question_works_after_analysis(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)
    analyze(client, dataset_id)

    response = ask(client, dataset_id, "what charts should I use?")

    assert response["intent"] == "chart_help"
    assert response["result"]["data"]


def test_forecast_readiness_question_works_after_analysis(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)
    analyze(client, dataset_id)

    response = ask(client, dataset_id, "can I forecast sales?")

    assert response["intent"] == "forecast_help"
    assert "sales" in response["answer"]


def test_unsupported_question_returns_useful_response(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)

    response = ask(client, dataset_id, "write me a poem")

    assert response["intent"] == "unsupported"
    assert "I can answer" in response["answer"]


def test_ambiguous_column_name_returns_clarification(client: TestClient) -> None:
    dataset_id = upload_chat_csv(
        client,
        b"sale,sales\n1,10\n2,20\n",
        "ambiguous.csv",
    )

    response = ask(client, dataset_id, "average sal")

    assert response["intent"] == "clarification"
    assert "sale" in response["result"]["data"]
    assert "sales" in response["result"]["data"]


def test_user_provided_code_like_message_is_not_executed(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)

    response = ask(client, dataset_id, "run python print('hello')")

    assert response["intent"] == "unsupported"
    assert response["warnings"]


def test_response_is_json_safe_with_no_nan_or_inf(client: TestClient) -> None:
    dataset_id = upload_chat_csv(client)
    analyze(client, dataset_id)

    response = ask(client, dataset_id, "average sales by region")

    json.dumps(response)
    assert_no_nan(response)
