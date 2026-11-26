
from uuid import uuid4

from agent.graph.workflow import build_graph

graph = build_graph()
thread_id = f"hotel-debug-{uuid4().hex}"

messages = [
    "I want to book a hotel in Riyadh",
    "check in 1 dec check out 5 dec 4 guests 2 rooms",
]

for message in messages:
    print("\n" + "=" * 60)
    print("USER:", message)

    result = graph.invoke(
        {
            "user_id": "USER-001",
            "session_id": thread_id,
            "user_message": message,
            "language": "en",
        },
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

    for field in (
        "intent",
        "status",
        "destination",
        "check_in_date",
        "check_out_date",
        "guests",
        "rooms",
        "missing_fields",
        "validation_errors",
        "hotel_request",
        "response",
    ):
        print(f"{field}: {result.get(field)}")
