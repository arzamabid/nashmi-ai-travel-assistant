
from agent.graph.state import NashmiState
from tools.restaurant_availability_tools import (
    check_restaurant_availability,
)
from tools.schemas.restaurant_availability import (
    RestaurantAvailabilityRequest,
)


def check_restaurant_options_node(state: NashmiState):
    request_data = state.get("restaurant_request") or {}
    restaurants = state.get("search_results") or []

    required = ["date", "time", "party_size"]

    if any(request_data.get(key) is None for key in required):
        return {
            "status": "missing_restaurant_parameters",
            "available_restaurants": [],
        }

    available_restaurants = []

    for restaurant in restaurants:
        request = RestaurantAvailabilityRequest(
            restaurant_id=restaurant["restaurant_id"],
            date=request_data["date"],
            time=request_data["time"],
            party_size=request_data["party_size"],
        )

        availability = check_restaurant_availability(request)

        if availability.available:
            available_restaurants.append(restaurant)

    return {
        "status": "restaurant_availability_checked",
        "available_restaurants": available_restaurants,
    }
