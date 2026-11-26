
from pydantic import ValidationError

from agent.graph.state import NashmiState
from agent.llm.restaurant_extractor import extract_restaurant_parameters
from agent.utils.merge import merge_parameters
from tools.schemas.common import RestaurantSearchRequest
from tools.schemas.restaurant_availability import RestaurantAvailabilityRequest
from agent.utils.locations import normalize_location_fields


def extract_restaurant_node(state: NashmiState):
    extracted = extract_restaurant_parameters(
        state["user_message"]
    )

    previous = state.get("restaurant_request")
    combined = merge_parameters(previous, extracted)
    combined = normalize_location_fields(combined)

    required = ["city", "date", "time", "party_size"]

    missing = [
        field for field in required
        if combined.get(field) is None or combined.get(field) == ""
    ]

    if missing:
        return {
            "restaurant_request": combined,
            "missing_fields": missing,
            "status": "missing_restaurant_parameters",
        }

    try:
        RestaurantSearchRequest.model_validate(combined)

        # Validate the availability-specific fields separately.
        # This validates their types and any rules in your schema.
        RestaurantAvailabilityRequest.model_validate({
            "restaurant_id": "PENDING_SELECTION",
            "date": combined["date"],
            "time": combined["time"],
            "party_size": combined["party_size"],
        })

    except ValidationError as exc:
        return {
            "restaurant_request": combined,
            "status": "invalid_restaurant_parameters",
            "validation_errors": exc.errors(),
        }

    return {
        "restaurant_request": combined,
        "missing_fields": [],
        "validation_errors": [],
        "status": "restaurant_parameters_extracted",
    }


def ask_restaurant_follow_up(state: NashmiState):
    missing = state.get("missing_fields", [])

    return {
        "status": "awaiting_restaurant_details",
        "response": (
            "Please provide: " + ", ".join(missing)
        ),
    }
