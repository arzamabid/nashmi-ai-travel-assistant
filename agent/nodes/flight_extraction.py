
from pydantic import ValidationError

from agent.graph.state import NashmiState
from agent.llm.flight_extractor import extract_flight_parameters
from agent.utils.merge import merge_parameters
from tools.schemas.flight import FlightSearchRequest
from agent.utils.locations import normalize_location_fields
from agent.utils.flight_parameters import normalize_flight_parameters
from agent.utils.flight_followups import apply_flight_followup

def extract_flight_node(state: NashmiState):
    extracted = extract_flight_parameters(
        state["user_message"]
    )

    extracted = normalize_flight_parameters(
        state["user_message"],
        extracted,
    )

    extracted = apply_flight_followup(
        message=state["user_message"],
        extracted=extracted,
        previous_request=state.get("flight_request"),
        missing_fields=state.get("missing_fields"),
    )

    previous = state.get("flight_request")
    combined = merge_parameters(previous, extracted)
    combined = normalize_location_fields(combined)

    required = [
        "origin",
        "destination",
        "departure_date",
        "passengers",
    ]

    missing = [
        field for field in required
        if combined.get(field) is None
        or combined.get(field) == ""
    ]

    if missing:
        return {
            "flight_request": combined,
            "missing_fields": missing,
            "validation_errors": [],
            "status": "missing_flight_parameters",
        }

    try:
        FlightSearchRequest.model_validate(combined)

    except ValidationError as exc:
        return {
            "flight_request": combined,
            "missing_fields": [],
            "validation_errors": exc.errors(),
            "status": "invalid_flight_parameters",
        }

    return {
        "flight_request": combined,
        "missing_fields": [],
        "validation_errors": [],
        "status": "flight_parameters_extracted",
    }


def ask_flight_follow_up(state: NashmiState):
    missing = state.get("missing_fields", [])

    return {
        "status": "awaiting_flight_details",
        "response": (
            "Please provide: " + ", ".join(missing)
        ),
    }
