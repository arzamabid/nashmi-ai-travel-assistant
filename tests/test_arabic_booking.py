
from types import SimpleNamespace

import pytest

import agent.nodes.booking_confirmation as booking_module
from agent.nodes.booking_confirmation import confirm_booking_node


def pending_booking_state(message):
    return {
        "user_id": "USER-001",
        "user_message": message,
        "language": "ar",
        "status": "awaiting_booking_confirmation",
        "booking_preview_id": "PREVIEW-AR-001",
        "selected_item_id": "FLT-005",
        "selected_service_type": "flight",
        "user_confirmed": False,
    }


@pytest.mark.parametrize(
    "message",
    [
        "نعم، أكد الحجز",
        "أؤكد الحجز",
        "تأكيد الحجز",
    ],
)
def test_arabic_explicit_confirmation(monkeypatch, message):
    confirmation_calls = []

    def fake_confirm(request):
        confirmation_calls.append(request)
        return SimpleNamespace(
            booking_id=request.preview_id,
            item_id="FLT-005",
            status="confirmed",
            confirmed=True,
        )

    monkeypatch.setattr(
        booking_module,
        "confirm_flight_booking",
        fake_confirm,
    )

    result = confirm_booking_node(
        pending_booking_state(message)
    )

    assert result["status"] == "booking_confirmed"
    assert result["user_confirmed"] is True
    assert result["booking_preview_id"] == ""

    assert len(confirmation_calls) == 1
    assert confirmation_calls[0].user_id == "USER-001"
    assert confirmation_calls[0].confirmed is True


def test_arabic_ambiguous_approval_rejected(monkeypatch):
    confirmation_calls = []

    def fake_confirm(request):
        confirmation_calls.append(request)

    monkeypatch.setattr(
        booking_module,
        "confirm_flight_booking",
        fake_confirm,
    )

    result = confirm_booking_node(
        pending_booking_state("نعم")
    )

    assert result["status"] == "awaiting_booking_confirmation"
    assert result["user_confirmed"] is False
    assert confirmation_calls == []


@pytest.mark.parametrize(
    "message",
    [
        "لا، ألغِ الحجز",
        "لا أريد الحجز",
    ],
)
def test_arabic_booking_cancellation(monkeypatch, message):
    cancellation_calls = []

    def fake_cancel(preview_id, user_id):
        cancellation_calls.append((preview_id, user_id))
        return "cancelled"

    monkeypatch.setattr(
        booking_module,
        "cancel_booking_preview",
        fake_cancel,
    )

    result = confirm_booking_node(
        pending_booking_state(message)
    )

    assert result["status"] == "booking_preview_cancelled"
    assert result["booking_preview_id"] == ""
    assert result["user_confirmed"] is False

    assert cancellation_calls == [
        ("PREVIEW-AR-001", "USER-001")
    ]


def test_arabic_confirmation_without_pending_preview(monkeypatch):
    confirmation_calls = []

    def fake_confirm(request):
        confirmation_calls.append(request)

    monkeypatch.setattr(
        booking_module,
        "confirm_flight_booking",
        fake_confirm,
    )

    state = pending_booking_state("نعم، أكد الحجز")
    state["booking_preview_id"] = ""

    result = confirm_booking_node(state)

    assert result["status"] == "booking_confirmation_rejected"
    assert confirmation_calls == []
