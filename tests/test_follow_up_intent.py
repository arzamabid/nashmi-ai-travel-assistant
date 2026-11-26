
from agent.nodes.intent import classify_intent


def test_hotel_follow_up():
    state = {
        "user_message": "December 10 to 12, two guests",
        "intent": "hotel_search",
        "status": "awaiting_hotel_details",
    }

    result = classify_intent(state)

    assert result["intent"] == "hotel_search"


def test_switch_to_flight():
    state = {
        "user_message": "Actually find a flight to Dubai",
        "intent": "hotel_search",
        "status": "awaiting_hotel_details",
    }

    result = classify_intent(state)

    assert result["intent"] == "flight_search"


def test_new_conversation_unknown():
    state = {
        "user_message": "Hello",
    }

    result = classify_intent(state)

    assert result["intent"] == "unknown"



def test_unrelated_message_does_not_continue_hotel():
    state = {
        "user_message": "What's the weather today?",
        "intent": "hotel_search",
        "status": "awaiting_hotel_details",
    }

    result = classify_intent(state)

    assert result["intent"] == "unknown"


def test_hotel_date_follow_up():
    state = {
        "user_message": "December 10 to 12, two guests",
        "intent": "hotel_search",
        "status": "awaiting_hotel_details",
    }

    result = classify_intent(state)

    assert result["intent"] == "hotel_search"
