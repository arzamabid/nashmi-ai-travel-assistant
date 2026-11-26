
from agent.nodes.intent import classify_intent


def test_old_hotel_question_is_cleared():
    state = {
        "user_message": (
            "check in 1 dec check out 5 dec "
            "4 guests 2 rooms"
        ),
        "intent": "hotel_search",
        "status": "awaiting_hotel_details",
        "hotel_request": {
            "destination": "Riyadh",
        },
        "response": (
            "What is your check-in date? "
            "What is your check-out date?"
        ),
    }

    result = classify_intent(state)

    assert result["intent"] == "hotel_search"
    assert result["response"] == ""
