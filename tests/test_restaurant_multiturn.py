
from unittest.mock import patch
from uuid import uuid4

from agent.graph.workflow import build_graph
from tools.schemas.common import RestaurantSearchResult


def test_restaurant_multiturn():
    graph = build_graph()

    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    first_extraction = {
        "city": "Riyadh",
        "cuisine": "Italian",
        "price_level": None,
        "family_friendly": None,
        "date": None,
        "time": None,
        "party_size": None,
    }

    second_extraction = {
        "city": None,
        "cuisine": None,
        "price_level": None,
        "family_friendly": None,
        "date": "2026-11-23",
        "time": "20:00",
        "party_size": 4,
    }

    restaurant = RestaurantSearchResult(
        restaurant_id="REST-001",
        name="Bella Italia",
        city="Riyadh",
        cuisine="Italian",
        price_level="Moderate",
        family_friendly=True,
    )

    with (
        patch(
            "agent.nodes.restaurant_extraction."
            "extract_restaurant_parameters",
            side_effect=[
                first_extraction,
                second_extraction,
            ],
        ),
        patch(
            "agent.graph.workflow.search_restaurants",
            return_value=[restaurant],
        ),
    ):
        first = graph.invoke(
            {
                "user_message": (
                    "Find an Italian restaurant in Riyadh"
                ),
            },
            config=config,
        )

        assert first["status"] == "awaiting_restaurant_details"
        assert set(first["missing_fields"]) == {
            "date", "time", "party_size"
        }

        second = graph.invoke(
            {
                "user_message": (
                    "Tomorrow at 8 PM for four people"
                ),
            },
            config=config,
        )

    assert second["status"] == "restaurant_availability_checked"
    assert second["restaurant_request"]["city"] == "Riyadh"
    assert second["restaurant_request"]["party_size"] == 4
    assert second["restaurant_request"]["time"] == "20:00"
    assert second["search_results"][0]["name"] == "Bella Italia"
