
import re

from agent.graph.state import NashmiState


def is_hotel_follow_up(message: str) -> bool:
    message = message.lower()

    follow_up_words = [
        "guest", "guests",
        "room", "rooms",
        "night", "nights",
        "check-in", "check-out",
        "star", "stars",
        "budget", "sar",
        "tomorrow", "tonight",
        "december", "january",
        "february", "march",
        "april", "may", "june",
        "july", "august",
        "september", "october",
        "november",
    ]

    return (
        any(word in message for word in follow_up_words)
        or bool(re.search(r"\b\d{4}-\d{2}-\d{2}\b", message))
    )


def is_restaurant_follow_up(message: str) -> bool:
    message = message.lower()

    follow_up_words = [
        "tomorrow", "today", "tonight",
        "people", "person", "party",
        "guest", "guests", "table",
        "italian", "japanese",
        "riyadh", "jeddah",
        "pm", "am",
    ]

    return (
        any(word in message for word in follow_up_words)
        or bool(re.search(r"\b\d{4}-\d{2}-\d{2}\b", message))
        or bool(re.search(r"\b\d{1,2}:\d{2}\b", message))
    )



def is_flight_follow_up(message: str) -> bool:
    message = message.lower()

    follow_up_words = [
        "tomorrow", "today", "tonight",
        "flight", "flights",
        "passenger", "passengers",
        "person", "people",
        "date", "departure",
        "destination",
        "direct", "nonstop",
        "cabin", "economy", "business",
        "riyadh", "dubai", "jeddah",
        "pm", "am",
        "january", "february", "march",
        "april", "may", "june",
        "july", "august", "september",
        "october", "november", "december",
    ]

    return (
        any(
            re.search(rf"\b{re.escape(word)}\b", message)
            for word in follow_up_words
        )
        or bool(
            re.search(r"\b\d{4}-\d{2}-\d{2}\b", message)
        )
        or bool(
            re.search(r"\b\d{1,2}:\d{2}\b", message)
        )
    )


def is_flight_date_refinement(message: str) -> bool:
    message = message.lower().strip()

    months = (
        "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "sept", "oct",
        "nov", "dec",
    )

    month_pattern = "|".join(
        rf"{month}[a-z]*" for month in months
    )

    return bool(
        re.search(
            rf"\b\d{{1,2}}\s+(?:{month_pattern})\b",
            message,
        )
        or re.search(
            r"\b\d{4}-\d{2}-\d{2}\b",
            message,
        )
    )


def _classify_intent_impl(state: NashmiState) -> dict:
    user_message = state.get("user_message", "").lower().strip()

    previous_intent = state.get("intent")
    previous_status = state.get("status")

    # Detect an explicit new search while a booking
    # preview is awaiting confirmation.
    if (
        previous_status == "awaiting_booking_confirmation"
        and state.get("booking_preview_id")
    ):
        search_pattern = (
            r"\b(?:find|search(?: for)?|show|look for)\b"
            r".*\b(hotels?|flights?|restaurants?)\b"
        )

        match = re.search(search_pattern, user_message)

        if match:
            service_word = match.group(1)

            if service_word.startswith("hotel"):
                target_intent = "hotel_search"

            elif service_word.startswith("flight"):
                target_intent = "flight_search"

            else:
                target_intent = "restaurant_search"

            return {
                "intent": "search_switch",
                "requested_search_intent": target_intent,
            }

    # 1. Pending booking confirmation takes priority.
    if (
        previous_status == "awaiting_booking_confirmation"
        and state.get("booking_preview_id")
    ):
        return {"intent": "booking_confirmation"}

    # 2. Detect selection of an available option.
    selection_pattern = (
        r"\b(?:first|second|third|fourth|fifth)\b"
        r"|\b(?:option|flight|hotel|restaurant|number)"
        r"\s*#?\s*\d+\b"
    )

    is_selection = bool(
        re.search(selection_pattern, user_message)
    )

    if is_selection:
        if previous_status in {
            "hotel_availability_checked",
            "restaurant_availability_checked",
            "awaiting_service_selection",
            "invalid_service_selection",
        }:
            if previous_status == "hotel_availability_checked":
                service = "hotel"

            elif previous_status == "restaurant_availability_checked":
                service = "restaurant"

            else:
                service = state.get("selected_service_type")

            if service in {"hotel", "restaurant"}:
                return {
                    "intent": "service_selection",
                    "selected_service_type": service,
                }

        if previous_status in {
            "flight_availability_checked",
            "awaiting_flight_selection",
            "invalid_flight_selection",
        }:
            return {"intent": "flight_selection"}


    # Allow flight date changes after an availability
    # search, including a search with zero results.
    if (
        previous_intent == "flight_search"
        and previous_status == "flight_availability_checked"
        and state.get("flight_request")
        and not state.get("available_flights")
        and is_flight_date_refinement(user_message)
    ):
        return {"intent": "flight_search"}


    # 3. Detect explicit English and Arabic search requests.
    restaurant_words = (
        "restaurant",
        "مطعم",
        "مطاعم",
    )

    flight_words = (
        "flight",
        "flights",
        "رحلة",
        "رحلات",
        "طيران",
        "تذكرة طيران",
    )

    hotel_words = (
        "hotel",
        "hotels",
        "فندق",
        "فنادق",
    )

    if any(word in user_message for word in restaurant_words):
        intent = "restaurant_search"

    elif any(word in user_message for word in flight_words):
        intent = "flight_search"

    elif any(word in user_message for word in hotel_words):
        intent = "hotel_search"

    # elif "flight" in user_message:
    #     intent = "flight_search"
    #
    # elif "hotel" in user_message:
    #     intent = "hotel_search"


    # 4. Continue unfinished searches.
    # Explicit new-search requests above take priority.

    elif (

            previous_intent == "hotel_search"

            and previous_status == "awaiting_hotel_details"

            and is_hotel_follow_up(user_message)

    ):

        intent = "hotel_search"

    elif (
        previous_intent == "restaurant_search"
        and previous_status == "awaiting_restaurant_details"
    ):
        intent = "restaurant_search"

    elif (
        previous_intent == "flight_search"
        and previous_status == "awaiting_flight_details"
    ):
        intent = "flight_search"

    else:
        intent = "unknown"

    return {"intent": intent}


def classify_intent(state: NashmiState) -> dict:
    """
    Preserve existing intent logic while clearing
    response text from the previous user turn.
    """
    result = _classify_intent_impl(state)

    return {
        **result,
        "response": "",
    }
