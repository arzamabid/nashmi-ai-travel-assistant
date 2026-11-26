
import pytest
from pydantic import ValidationError

from tools.hotel_availability_tools import check_hotel_availability
from tools.schemas.hotel_availability import HotelAvailabilityRequest


def test_hotel_availability_rejects_invalid_dates():
    with pytest.raises(ValidationError):
        HotelAvailabilityRequest(
            hotel_id="HTL-RYD-001",
            check_in_date="2026-12-15",
            check_out_date="2026-12-10",
            guests=2,
            rooms=1,
        )


def test_hotel_availability_returns_false_for_unknown_hotel():
    request = HotelAvailabilityRequest(
        hotel_id="UNKNOWN",
        check_in_date="2026-12-10",
        check_out_date="2026-12-12",
        guests=2,
        rooms=1,
    )

    result = check_hotel_availability(request)

    assert result.hotel_id == "UNKNOWN"
    assert result.available is False


def test_hotel_availability_returns_false_when_inventory_missing():
    request = HotelAvailabilityRequest(
        hotel_id="HTL-RYD-001",
        check_in_date="2027-02-10",
        check_out_date="2027-02-12",
        guests=2,
        rooms=1,
    )

    result = check_hotel_availability(request)

    assert result.available is False




def test_hotel_availability_returns_true_for_seeded_rooms():
    request = HotelAvailabilityRequest(
        hotel_id="HTL-RYD-001",
        check_in_date="2026-12-10",
        check_out_date="2026-12-13",
        guests=2,
        rooms=1,
    )

    result = check_hotel_availability(request)

    assert result.hotel_id == "HTL-RYD-001"
    assert result.available is True
