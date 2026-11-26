
from agent.graph.state import NashmiState
from tools.booking_tools import cancel_booking_preview


SEARCH_CONFIG = {
    "flight_search": {
        "request_key": "flight_request",
        "results_keys": [
            "flight_results",
            "available_flights",
        ],
    },
    "hotel_search": {
        "request_key": "hotel_request",
        "results_keys": [
            "hotel_results",
            "available_hotels",
        ],
    },
    "restaurant_search": {
        "request_key": "restaurant_request",
        "results_keys": [
            "search_results",
            "available_restaurants",
        ],
    },
}


def switch_search_node(state: NashmiState) -> dict:
    target_intent = state.get("requested_search_intent")
    config = SEARCH_CONFIG.get(target_intent)

    if config is None:
        return {
            "status": "search_switch_failed",
            "response": "Unsupported search request.",
        }

    preview_id = state.get("booking_preview_id")
    user_id = state.get("user_id")

    # Cancel the pending preview before switching.
    if preview_id:
        if not user_id:
            return {
                "status": "search_switch_failed",
                "response": "A valid user account is required.",
            }

        try:
            cancel_booking_preview(
                preview_id=preview_id,
                user_id=user_id,
            )
        except ValueError as error:
            return {
                "status": "search_switch_failed",
                "response": str(error),
            }

    # Clear the old booking selection and confirmation.
    updates = {
        "booking_preview_id": "",
        "selected_item_id": "",
        "selected_service_type": "",
        "user_confirmed": False,
        "missing_fields": [],
        "validation_errors": [],
        "availability_checked": False,
        "status": "search_switch_ready",
        "intent": target_intent,
        "response": "",
    }

    # Clear old target-service parameters so that a
    # genuinely new search cannot reuse stale dates,
    # destinations or guest counts.
    updates[config["request_key"]] = {}

    for key in config["results_keys"]:
        updates[key] = []

    return updates
