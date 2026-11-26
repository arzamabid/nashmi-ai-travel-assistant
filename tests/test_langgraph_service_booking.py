
from types import SimpleNamespace
from uuid import uuid4

import pytest

from agent.graph.workflow import build_graph
import agent.nodes.service_booking as service_booking
import agent.nodes.booking_confirmation as booking_confirmation


@pytest.mark.parametrize(
    "service, selection, results_key, request_key, id_key, details",
    [
        (
            "hotel",
            "the second hotel",
            "available_hotels",
            "hotel_request",
            "hotel_id",
            {
                "check_in_date": "2026-12-20",
                "check_out_date": "2026-12-22",
                "guests": 2,
                "rooms": 1,
            },
        ),
        (
            "restaurant",
            "restaurant 1",
            "available_restaurants",
            "restaurant_request",
            "restaurant_id",
            {
                "date": "2026-12-20",
                "time": "19:00",
                "party_size": 2,
            },
        ),
    ],
)
def test_multiturn_service_booking(
    monkeypatch,
    service,
    selection,
    results_key,
    request_key,
    id_key,
    details,
):
    preview_calls = []
    confirmation_calls = []

    options = [
        {id_key: f"TEST-{service.upper()}-001"},
        {id_key: f"TEST-{service.upper()}-002"},
    ]

    expected_index = 1 if service == "hotel" else 0
    expected_item_id = options[expected_index][id_key]
    preview_id = f"PREVIEW-TEST-{service.upper()}"

    def fake_create_preview(request):
        preview_calls.append(request)
        return SimpleNamespace(preview_id=preview_id)

    def fake_confirm(request):
        confirmation_calls.append(request)
        return SimpleNamespace(
            booking_id=request.preview_id,
            item_id=expected_item_id,
            status="confirmed",
            confirmed=True,
        )

    monkeypatch.setattr(
        service_booking,
        "create_booking_preview",
        fake_create_preview,
    )

    confirmation_function = (
        "confirm_hotel_booking"
        if service == "hotel"
        else "confirm_restaurant_booking"
    )

    monkeypatch.setattr(
        booking_confirmation,
        confirmation_function,
        fake_confirm,
    )

    graph = build_graph()

    config = {
        "configurable": {
            "thread_id": f"test-{uuid4().hex}"
        }
    }

    # Turn 1: Select an available option.
    first = graph.invoke(
        {
            "user_id": "USER-001",
            "user_message": selection,
            "intent": f"{service}_search",
            "status": f"{service}_availability_checked",
            results_key: options,
            request_key: details,
        },
        config=config,
    )

    assert first["status"] == (
        "awaiting_booking_confirmation"
    )

    assert first["selected_service_type"] == service
    assert first["selected_item_id"] == expected_item_id
    assert first["booking_preview_id"] == preview_id
    assert first["user_confirmed"] is False

    assert len(preview_calls) == 1
    assert preview_calls[0].service_type == service
    assert preview_calls[0].item_id == expected_item_id
    assert preview_calls[0].details == details

    # No confirmation should occur during selection.
    assert confirmation_calls == []

    # Turn 2: Explicitly approve the booking.
    second = graph.invoke(
        {
            "user_message": "Yes, confirm the booking",
        },
        config=config,
    )

    assert second["status"] == "booking_confirmed"
    assert second["user_confirmed"] is True
    assert second["booking_preview_id"] == ""

    assert len(confirmation_calls) == 1
    assert confirmation_calls[0].preview_id == preview_id
    assert confirmation_calls[0].user_id == "USER-001"
    assert confirmation_calls[0].confirmed is True
