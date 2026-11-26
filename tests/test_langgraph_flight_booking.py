
from types import SimpleNamespace
from uuid import uuid4

from agent.graph.workflow import build_graph
import agent.nodes.flight_booking as flight_booking
import agent.nodes.booking_confirmation as booking_confirmation


def test_multiturn_flight_booking(monkeypatch):
    preview_calls = []
    confirmation_calls = []

    def fake_create_preview(request):
        preview_calls.append(request)
        return SimpleNamespace(
            preview_id="PREVIEW-TEST-001"
        )

    def fake_confirm_booking(request):
        confirmation_calls.append(request)
        return SimpleNamespace(
            booking_id=request.preview_id,
            item_id="FLT-002",
            status="confirmed",
            confirmed=True,
        )

    monkeypatch.setattr(
        flight_booking,
        "create_booking_preview",
        fake_create_preview,
    )

    monkeypatch.setattr(
        booking_confirmation,
        "confirm_flight_booking",
        fake_confirm_booking,
    )

    graph = build_graph()

    config = {
        "configurable": {
            "thread_id": f"test-{uuid4().hex}"
        }
    }

    # Turn 1: User selects the second available flight.
    first_result = graph.invoke(
        {
            "user_id": "USER-001",
            "user_message": "the second one",
            "intent": "flight_search",
            "status": "flight_availability_checked",
            "flight_request": {
                "passengers": 2,
            },
            "available_flights": [
                {"flight_id": "FLT-001"},
                {"flight_id": "FLT-002"},
            ],
        },
        config=config,
    )

    assert first_result["status"] == (
        "awaiting_booking_confirmation"
    )
    assert first_result["selected_item_id"] == "FLT-002"
    assert first_result["booking_preview_id"] == (
        "PREVIEW-TEST-001"
    )
    assert first_result["user_confirmed"] is False

    assert len(preview_calls) == 1
    assert preview_calls[0].item_id == "FLT-002"
    assert preview_calls[0].details["passengers"] == 2

    # Turn 2: User explicitly confirms.
    # The same thread_id preserves conversation state.
    second_result = graph.invoke(
        {
            "user_message": "Yes, confirm the booking",
        },
        config=config,
    )

    assert second_result["status"] == "booking_confirmed"
    assert second_result["user_confirmed"] is True

    assert len(confirmation_calls) == 1
    assert confirmation_calls[0].preview_id == (
        "PREVIEW-TEST-001"
    )
    assert confirmation_calls[0].confirmed is True

    # Booking preview must no longer be pending.
    assert second_result["booking_preview_id"] == ""

def test_booking_requires_explicit_approval(monkeypatch):
    from types import SimpleNamespace
    from uuid import uuid4

    from agent.graph.workflow import build_graph
    import agent.nodes.flight_booking as flight_booking
    import agent.nodes.booking_confirmation as booking_confirmation

    confirmation_calls = []

    def fake_preview(request):
        return SimpleNamespace(
            preview_id="PREVIEW-SAFETY-TEST"
        )

    def fake_confirm(request):
        confirmation_calls.append(request)
        return SimpleNamespace(
            booking_id=request.preview_id,
            item_id="FLT-001",
            status="confirmed",
            confirmed=True,
        )

    monkeypatch.setattr(
        flight_booking,
        "create_booking_preview",
        fake_preview,
    )

    monkeypatch.setattr(
        booking_confirmation,
        "confirm_flight_booking",
        fake_confirm,
    )

    graph = build_graph()

    config = {
        "configurable": {
            "thread_id": f"safety-{uuid4().hex}"
        }
    }

    # Turn 1: Select a flight.
    first = graph.invoke(
        {
            "user_id": "USER-001",
            "user_message": "the first one",
            "intent": "flight_search",
            "status": "flight_availability_checked",
            "flight_request": {"passengers": 2},
            "available_flights": [
                {"flight_id": "FLT-001"}
            ],
        },
        config=config,
    )

    assert first["status"] == "awaiting_booking_confirmation"

    # Turn 2: Ambiguous approval must not book.
    second = graph.invoke(
        {"user_message": "Yes"},
        config=config,
    )

    assert second["status"] == "awaiting_booking_confirmation"
    assert second["user_confirmed"] is False
    assert confirmation_calls == []

    # Turn 3: Explicit approval may book.
    third = graph.invoke(
        {"user_message": "Yes, confirm the booking"},
        config=config,
    )

    assert third["status"] == "booking_confirmed"
    assert third["user_confirmed"] is True
    assert len(confirmation_calls) == 1

    # Turn 4: Approval cannot reuse a completed preview.
    fourth = graph.invoke(
        {"user_message": "Yes, confirm the booking"},
        config=config,
    )

    assert len(confirmation_calls) == 1
    assert fourth["booking_preview_id"] == ""
