from agent.graph.state import NashmiState


def start_session(state: NashmiState) -> dict:
    # Only initialize the status for a new conversation.
    # Do not overwrite the status of an existing conversation.

    if state.get("status") is None:
        return {
            "status": "session_started"
        }

    return {}
