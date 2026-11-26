
from unittest.mock import patch

from agent.nodes.hotel_availability import (
    check_hotel_availability_node,
)
from tools.schemas.hotel_availability import (
    HotelAvailabilityResult,
)


def test_hotel_availability_node_filters_hotels():
    state = {
        "hotel_request": {
            "destination": "Riyadh",
            "check_in_date": "2026-12-10",
            "check_out_date": "2026-12-12",
            "guests": 2,
            "rooms": 1,
        },
        "hotel_results": [
            {
                "hotel_id": "HTL-RYD-001",
                "name": "Hotel A",
            },
            {
                "hotel_id": "HTL-RYD-002",
                "name": "Hotel B",
            },
        ],
    }

    def fake_availability(request):
        return HotelAvailabilityResult(
            hotel_id=request.hotel_id,
            check_in_date="2026-12-10",
            check_out_date="2026-12-12",
            guests=2,
            rooms=1,
            available=request.hotel_id == "HTL-RYD-001",
        )

    with patch(
        "agent.nodes.hotel_availability.check_hotel_availability",
        side_effect=fake_availability,
    ):
        result = check_hotel_availability_node(state)

    assert result["status"] == "hotel_availability_checked"
    assert len(result["available_hotels"]) == 1
    assert result["available_hotels"][0]["hotel_id"] == "HTL-RYD-001"


def test_hotel_availability_node_handles_empty_results():
    state = {
        "hotel_request": {
            "destination": "Riyadh",
            "check_in_date": "2026-12-10",
            "check_out_date": "2026-12-12",
            "guests": 2,
            "rooms": 1,
        },
        "hotel_results": [],
    }

    result = check_hotel_availability_node(state)

    assert result["status"] == "hotel_search_completed"
    assert result["available_hotels"] == []
