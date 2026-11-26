
from agent.graph.state import NashmiState

from tools.hotel_availability_tools import (
    check_hotel_availability,
)

from tools.schemas.hotel_availability import (
    HotelAvailabilityRequest,
)


def check_hotel_availability_node(
    state: NashmiState,
) -> dict:

    hotel_request = state.get("hotel_request")
    hotel_results = state.get("hotel_results", [])

    if not hotel_request:
        return {
            "status": "missing_hotel_parameters",
            "available_hotels": [],
        }

    if not hotel_results:
        return {
            "status": "hotel_search_completed",
            "available_hotels": [],
        }

    available_hotels = []

    for hotel in hotel_results:
        request = HotelAvailabilityRequest(
            hotel_id=hotel["hotel_id"],
            check_in_date=hotel_request["check_in_date"],
            check_out_date=hotel_request["check_out_date"],
            guests=hotel_request["guests"],
            rooms=hotel_request["rooms"],
        )

        result = check_hotel_availability(request)

        if result.available:
            available_hotels.append(hotel)

    return {
        "status": "hotel_availability_checked",
        "available_hotels": available_hotels,
    }
