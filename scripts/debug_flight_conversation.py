
from uuid import uuid4

from agent.graph.workflow import build_graph

graph = build_graph()
thread_id = f"flight-debug-{uuid4().hex}"

messages = [
    "I want to find a flight",
    "riyadh to abha 20 dec 2",
    "2",
    "riyadh to abha 20 dec 2 guests",
]

config = {
    "configurable": {
        "thread_id": thread_id,
    }
}

for message in messages:
    print("\n" + "=" * 60)
    print("USER:", message)

    try:
        result = graph.invoke(
            {
                "user_id": "USER-001",
                "session_id": thread_id,
                "user_message": message,
                "language": "en",
            },
            config=config,
        )

        for key in (
            "intent",
            "status",
            "requested_search_intent",
            "flight_request",
            "missing_fields",
            "validation_errors",
            "flight_results",
            "available_flights",
            "response",
        ):
            print(f"{key}: {result.get(key)}")

    except Exception as error:
        print(
            "EXCEPTION:",
            type(error).__name__,
            str(error),
        )
        raise
