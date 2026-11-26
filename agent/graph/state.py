
from typing import TypedDict, NotRequired


class NashmiState(TypedDict, total=False):
    # Session
    session_id: str
    user_id: str
    language: str
    intent: str
    user_message: str

    # Restaurant parameters
    city: str
    date: str
    time: str
    party_size: int

    restaurant_request: dict
    available_restaurants: list[dict]

    # Flight parameters
    origin: str
    destination: str
    departure_date: str
    passengers: int
    cabin: str
    direct_only: bool

    flight_request: dict
    flight_results: list[dict]

    available_flights: list[dict]

    # Hotel parameters
    check_in_date: str
    check_out_date: str
    guests: int
    rooms: int

    available_hotels: list[dict]

    hotel_request: NotRequired[dict | None]
    hotel_results: NotRequired[list[dict]]

    # Extraction and follow-up
    missing_fields: list[str]
    validation_errors: list[dict]
    response: str

    # Search and selection
    selected_item_id: str
    selected_service_type: str
    search_results: list
    availability_checked: bool

    # Booking
    booking_preview_id: str
    user_confirmed: bool

    # Workflow
    status: str
    error: str

    # Switching between searches
    requested_search_intent: str
