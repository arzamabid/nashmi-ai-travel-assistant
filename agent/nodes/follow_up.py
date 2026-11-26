
from agent.graph.state import NashmiState


FIELD_QUESTIONS = {
    "destination": "Which city are you visiting?",
    "check_in_date": "What is your check-in date?",
    "check_out_date": "What is your check-out date?",
    "guests": "How many guests are travelling?",
    "rooms": "How many rooms do you need?",
}


def ask_hotel_follow_up(state: NashmiState) -> dict:
    missing = state.get("missing_fields", [])

    questions = [
        FIELD_QUESTIONS[field]
        for field in missing
        if field in FIELD_QUESTIONS
    ]

    return {
        "response": " ".join(questions),
        "status": "awaiting_hotel_details",
    }
