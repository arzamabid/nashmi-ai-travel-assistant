
from unittest.mock import patch

from agent.graph.workflow import build_graph


def test_invalid_hotel_parameters():
    fake_llm_output = {
        "destination": "Jeddah",
        "check_in_date": "2026-12-10",
        "check_out_date": "2026-12-12",
        "guests": -2,
        "rooms": 1,
        "stars": 5,
        "max_budget_sar": 800,
    }

    with patch(
        "agent.nodes.hotel_extraction.extract_hotel_parameters",
        return_value=fake_llm_output,
    ) as mock_extract:

        graph = build_graph()

        result = graph.invoke({
            "user_message": "Find a hotel in Jeddah",

        },
        config = {
            "configurable": {
                "thread_id": "test-invalid-hotel"
            }
        },
        )

    assert result["intent"] == "hotel_search"
    assert result["status"] == "invalid_hotel_parameters"
    assert result["validation_errors"]
    assert not result.get("hotel_results")
    mock_extract.assert_called_once()


def test_missing_hotel_parameters():
    fake_llm_output = {
        "destination": "Jeddah",
        "check_in_date": None,
        "check_out_date": None,
        "guests": 2,
        "rooms": None,
        "stars": 5,
        "max_budget_sar": 800,
    }

    with patch(
        "agent.nodes.hotel_extraction.extract_hotel_parameters",
        return_value=fake_llm_output,
    ) as mock_extract:
        graph = build_graph()

        result = graph.invoke({
            "user_message": "Find a five-star hotel in Jeddah"
        },
            config={
                "configurable": {
                    "thread_id": "test-missing-hotel"
                }
            },
        )

    assert result["status"] == "awaiting_hotel_details"
    assert set(result["missing_fields"]) == {
        "check_in_date",
        "check_out_date",
        "rooms",
    }
    assert not result.get("hotel_results")
    mock_extract.assert_called_once()
