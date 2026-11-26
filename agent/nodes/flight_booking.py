
import re

from agent.graph.state import NashmiState
from tools.booking_tools import create_booking_preview
from tools.schemas.booking import BookingPreviewRequest


def select_flight_and_preview(state: NashmiState) -> dict:
    message = state.get("user_message", "").strip().lower()
    available_flights = state.get("available_flights") or []
    flight_request = state.get("flight_request") or {}
    user_id = state.get("user_id")

    if not user_id:
        return {
            "status": "booking_error",
            "response": "A user account is required to book.",
        }

    if state.get("booking_preview_id") and state.get(
        "status"
    ) == "awaiting_booking_confirmation":
        return {
            "status": "awaiting_booking_confirmation",
            "response": (
                "A booking preview already exists. "
                "Please confirm or cancel it first."
            ),
        }

    if not available_flights:
        return {
            "status": "no_available_flights",
            "response": "No available flights to select.",
        }

    # Support simple numbered selections.
    words = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
    }

    selected_number = None

    for word, number in words.items():
        if re.search(rf"\b{word}\b", message):
            selected_number = number
            break

    if selected_number is None:
        match = re.search(
            r"\b(?:option|flight|number)\s*(\d+)\b",
            message,
        )

        if match:
            selected_number = int(match.group(1))

    if selected_number is None:
        return {
            "status": "awaiting_flight_selection",
            "response": (
                "Please select a flight by its number, "
                "for example: 'the second one' or 'flight 2'."
            ),
        }

    if not 1 <= selected_number <= len(available_flights):
        return {
            "status": "invalid_flight_selection",
            "response": "That flight number is not available.",
        }

    selected_flight = available_flights[selected_number - 1]

    passengers = flight_request.get("passengers")

    if (
        not isinstance(passengers, int)
        or isinstance(passengers, bool)
        or passengers <= 0
    ):
        return {
            "status": "missing_flight_parameters",
            "response": "Please provide a valid passenger count.",
        }

    request = BookingPreviewRequest(
        user_id=user_id,
        service_type="flight",
        item_id=selected_flight["flight_id"],
        details={"passengers": passengers},
    )

    try:
        result = create_booking_preview(request)
    except ValueError as error:
        return {
            "status": "booking_preview_failed",
            "response": str(error),
        }

    return {
        "selected_item_id": selected_flight["flight_id"],
        "selected_service_type": "flight",
        "booking_preview_id": result.preview_id,
        "user_confirmed": False,
        "status": "awaiting_booking_confirmation",
        "response": (
            f"Flight {selected_flight['flight_id']} selected "
            f"for {passengers} passenger(s). "
            f"Booking preview {result.preview_id} is ready. "
            "Would you like to confirm this booking?"
        ),
    }
