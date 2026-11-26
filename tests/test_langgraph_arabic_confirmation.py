
from types import SimpleNamespace
from uuid import uuid4

import pytest

import agent.nodes.booking_confirmation as booking_module
from agent.graph.workflow import build_graph


@pytest.mark.parametrize(
    "message, expected_status, expected_text",
    [
        (
            "نعم",
            "awaiting_booking_confirmation",
            "لتأكيد الحجز",
        ),
        (
            "نعم، أكد الحجز",
            "booking_confirmed",
            "تم تأكيد",
        ),
        (
            "لا، ألغِ الحجز",
            "booking_preview_cancelled",
            "تم إلغاء",
        ),
    ],
)
def test_arabic_booking_through_langgraph(
    monkeypatch,
    message,
    expected_status,
    expected_text,
):
    confirmation_calls = []
    cancellation_calls = []

    def fake_confirm(request):
        confirmation_calls.append(request)
        return SimpleNamespace(
            booking_id=request.preview_id,
            item_id="FLT-005",
            status="confirmed",
            confirmed=True,
        )

    def fake_cancel(preview_id, user_id):
        cancellation_calls.append((preview_id, user_id))
        return "cancelled"

    monkeypatch.setattr(
        booking_module,
        "confirm_flight_booking",
        fake_confirm,
    )

    monkeypatch.setattr(
        booking_module,
        "cancel_booking_preview",
        fake_cancel,
    )

    graph = build_graph()

    result = graph.invoke(
        {
            "user_id": "USER-001",
            "user_message": message,
            "language": "ar",
            "intent": "flight_selection",
            "status": "awaiting_booking_confirmation",
            "booking_preview_id": "PREVIEW-AR-001",
            "selected_service_type": "flight",
            "selected_item_id": "FLT-005",
            "user_confirmed": False,
        },
        config={
            "configurable": {
                "thread_id": f"arabic-{uuid4().hex}",
            }
        },
    )

    assert result["status"] == expected_status
    assert expected_text in result["response"]

    if expected_status == "booking_confirmed":
        assert len(confirmation_calls) == 1
        assert cancellation_calls == []

    elif expected_status == "booking_preview_cancelled":
        assert confirmation_calls == []
        assert len(cancellation_calls) == 1

    else:
        assert confirmation_calls == []
        assert cancellation_calls == []
        assert result["booking_preview_id"] == "PREVIEW-AR-001"
