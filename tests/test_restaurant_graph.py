
from unittest.mock import patch

from agent.graph.workflow import build_graph
from tools.schemas.common import RestaurantSearchResult

from tools.schemas.restaurant_availability import (
    RestaurantAvailabilityResult,
)



def test_restaurant_search_graph():
    fake_restaurant = RestaurantSearchResult(
        restaurant_id="REST-001",
        name="Bella Italia",
        city="Riyadh",
        cuisine="Italian",
        price_level="Moderate",
        family_friendly=True,
    )

    extracted_data = {
        "city": "Riyadh",
        "cuisine": None,
        "price_level": None,
        "family_friendly": None,
        "date": "2026-12-10",
        "time": "20:00",
        "party_size": 2,
    }

    def fake_availability(request):
        return RestaurantAvailabilityResult(
            restaurant_id=request.restaurant_id,
            date=request.date,
            time=request.time,
            party_size=request.party_size,
            available=True,
        )

    with (
        patch(
            "agent.nodes.restaurant_extraction.extract_restaurant_parameters",
            return_value=extracted_data,
        ),
        patch(
            "agent.graph.workflow.search_restaurants",
            return_value=[fake_restaurant],
        ),
        patch(
            "agent.nodes.restaurant_availability.check_restaurant_availability",
            side_effect=fake_availability,
        ),
    ):
        graph = build_graph()

        result = graph.invoke(
            {
                "user_message": (
                    "Find an Italian restaurant in Riyadh "
                    "on December 10 at 8 PM for 2 people"
                )
            },
            config={
                "configurable": {
                    "thread_id": "restaurant-graph-availability-test"
                }
            },
        )

    assert result["status"] == "restaurant_availability_checked"
    assert len(result["search_results"]) == 1
    assert len(result["available_restaurants"]) == 1

    assert result["available_restaurants"][0]["name"] == "Bella Italia"
