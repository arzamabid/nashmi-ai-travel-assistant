
from unittest.mock import patch

from agent.graph.workflow import build_graph



def test_hotel_search_integration():
    fake_llm_output = {
        "destination": "Jeddah",
        "check_in_date": "2026-12-10",
        "check_out_date": "2026-12-12",
        "guests": 2,
        "rooms": 1,
        "stars": 5,
        "max_budget_sar": 1000,
    }

    with patch(
        "agent.nodes.hotel_extraction.extract_hotel_parameters",
        return_value=fake_llm_output,
    ):
        graph = build_graph()

        result = graph.invoke(
            {
                "user_message": (
                    "Find a five-star hotel in Jeddah "
                    "for two guests and one room, "
                    "December 10 to 12, 2026, "
                    "under 1000 SAR per night."
                )
            },
            config={
                "configurable": {
                    "thread_id": "test-hotel-search-integration"
                }
            },
        )

    assert result["intent"] == "hotel_search"
    assert result["status"] == "hotel_availability_checked"
    assert result["missing_fields"] == []

    assert isinstance(result["hotel_results"], list)
    assert isinstance(result["available_hotels"], list)

    assert len(result["hotel_results"]) >= 1
    assert len(result["available_hotels"]) >= 1

    for hotel in result["available_hotels"]:
        assert hotel["city"].lower() == "jeddah"
        assert hotel["stars"] == 5
        assert hotel["price_per_night_sar"] <= 1000

    assert any(
        hotel["hotel_id"] == "HTL-JED-001"
        for hotel in result["available_hotels"]
    )



def test_hotel_search_missing_parameters():
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
    ):
        graph = build_graph()

        result = graph.invoke({
            "user_message": "Find me a five-star hotel in Jeddah"
        },
            config={
                "configurable": {
                    "thread_id": "test-hotel-search-missing"
                }
            }
        )

    assert result["intent"] == "hotel_search"
    assert result["status"] == "awaiting_hotel_details"

    assert set(result["missing_fields"]) == {
        "check_in_date",
        "check_out_date",
        "rooms",
    }

    assert "check-in date" in result["response"]
    assert "check-out date" in result["response"]
    assert "rooms" in result["response"]

    assert not result.get("hotel_results")
