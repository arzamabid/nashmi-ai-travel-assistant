
import re

from agent.graph.state import NashmiState
from tools.booking_tools import create_booking_preview
from tools.schemas.booking import BookingPreviewRequest


SERVICE_CONFIG = {
    "hotel": {
        "results_key": "available_hotels",
        "request_key": "hotel_request",
        "id_key": "hotel_id",
        "required_details": (
            "check_in_date",
            "check_out_date",
            "guests",
            "rooms",
        ),
    },
    "restaurant": {
        "results_key": "available_restaurants",
        "request_key": "restaurant_request",
        "id_key": "restaurant_id",
        "required_details": (
            "date",
            "time",
            "party_size",
        ),
    },
}


def get_selection_number(message: str):
    message = message.lower().strip()

    words = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
    }

    for word, number in words.items():
        if re.search(rf"\b{word}\b", message):
            return number

    match = re.search(
        r"\b(?:option|hotel|restaurant|number)\s*#?\s*(\d+)\b",
        message,
    )

    if match:
        return int(match.group(1))

    return None


def select_service_and_preview(
    state: NashmiState,
) -> dict:
    service_type = state.get("selected_service_type")

    if service_type not in SERVICE_CONFIG:
        return {
            "status": "invalid_service_selection",
            "response": "Unsupported booking service.",
        }

    config = SERVICE_CONFIG[service_type]

    user_id = state.get("user_id")

    if not user_id:
        return {
            "status": "booking_error",
            "response": "A user account is required to book.",
        }

    if (
        state.get("status") == "awaiting_booking_confirmation"
        and state.get("booking_preview_id")
    ):
        return {
            "status": "awaiting_booking_confirmation",
            "response": (
                "Please confirm or cancel your existing "
                "booking preview first."
            ),
        }

    options = state.get(config["results_key"]) or []
    request_data = state.get(config["request_key"]) or {}

    if not options:
        return {
            "status": "no_available_options",
            "response": (
                f"No available {service_type} options to select."
            ),
        }

    selected_number = get_selection_number(
        state.get("user_message", "")
    )

    if selected_number is None:
        return {
            "status": "awaiting_service_selection",
            "response": (
                f"Please choose a {service_type} by number, "
                "for example: 'the second one'."
            ),
        }

    if not 1 <= selected_number <= len(options):
        return {
            "status": "invalid_service_selection",
            "response": (
                f"That {service_type} option is not available."
            ),
        }

    selected_option = options[selected_number - 1]
    item_id = selected_option.get(config["id_key"])

    if not item_id:
        return {
            "status": "booking_error",
            "response": "The selected item has no valid ID.",
        }

    details = {
        key: request_data.get(key)
        for key in config["required_details"]
    }

    missing = [
        key
        for key, value in details.items()
        if value is None
    ]

    if missing:
        return {
            "status": "missing_booking_details",
            "response": (
                "Missing booking details: "
                + ", ".join(missing)
            ),
        }

    try:
        preview_request = BookingPreviewRequest(
            user_id=user_id,
            service_type=service_type,
            item_id=item_id,
            details=details,
        )

        result = create_booking_preview(preview_request)

    except ValueError as error:
        return {
            "status": "booking_preview_failed",
            "response": str(error),
        }

    return {
        "selected_item_id": item_id,
        "selected_service_type": service_type,
        "booking_preview_id": result.preview_id,
        "user_confirmed": False,
        "status": "awaiting_booking_confirmation",
        "response": (
            f"You selected {service_type} {item_id}. "
            f"Booking preview {result.preview_id} is ready. "
            "Would you like to confirm this booking?"
        ),
    }
