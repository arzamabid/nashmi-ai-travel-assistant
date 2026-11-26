
from agent.llm.hotel_extractor import extract_hotel_parameters
from tools.schemas.hotel import HotelSearchRequest
from pydantic import ValidationError
from agent.utils.merge import merge_parameters
from agent.utils.locations import normalize_location_fields
from agent.utils.travel_dates import normalize_hotel_dates
def extract_hotel_node(state: dict) -> dict:
    # Read the user's message from LangGraph State
    message = state["user_message"]

    # Ask Qwen to extract hotel details
    extracted = extract_hotel_parameters(message)
    extracted = normalize_hotel_dates(message, extracted)
    previous = state.get("hotel_request")

    combined = merge_parameters(
        previous=previous,
        new=extracted,
    )
    combined = normalize_location_fields(combined)

    # Check whether required information is missing
    required = [
        "destination",
        "check_in_date",
        "check_out_date",
        "guests",
        "rooms",
    ]

    missing_fields = [
        field for field in required
        if combined.get(field) is None
    ]

    if missing_fields:
        return {
            "hotel_request": combined,
            "status": "missing_hotel_parameters",
            "missing_fields": missing_fields,
        }

    # Validate the extracted data using Pydantic

    try:
        validated = HotelSearchRequest.model_validate(combined)
    except ValidationError as exc:
        return {
            "hotel_request": combined,
            "status": "invalid_hotel_parameters",
            "missing_fields": [],
            "validation_errors": exc.errors(
                include_context=False,
                include_input=False,
                include_url=False,
            ),
        }

    return {
        "hotel_request": combined,
        "missing_fields": missing_fields,
        "status": (
            "missing_hotel_parameters"
            if missing_fields
            else "hotel_parameters_extracted"
        ),
    }
