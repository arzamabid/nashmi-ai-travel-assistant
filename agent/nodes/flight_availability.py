
from agent.graph.state import NashmiState
from tools.flight_availability_tools import check_flight_availability
from tools.schemas.flight_availability import FlightAvailabilityRequest


def check_flight_options_node(state: NashmiState) -> dict:
    flight_results = state.get("flight_results", [])
    flight_request = state.get("flight_request") or {}

    passengers = flight_request.get("passengers")

    if not flight_results:
        return {
            "available_flights": [],
            "status": "flight_availability_checked",
        }

    if passengers is None:
        return {
            "available_flights": [],
            "status": "missing_flight_parameters",
        }

    available_flights = []

    for flight in flight_results:
        request = FlightAvailabilityRequest(
            flight_id=flight["flight_id"],
            passengers=passengers,
        )

        result = check_flight_availability(request)

        if result.available:
            available_flights.append({
                **flight,
                "available_seats": result.available_seats,
            })

    return {
        "available_flights": available_flights,
        "status": "flight_availability_checked",
    }
