
import pytest
from pydantic import ValidationError

from tools.schemas.hotel_availability import (
    HotelAvailabilityRequest,
)



def test_valid_hotel_availability_request():
    request = HotelAvailabilityRequest(
        hotel_id="HOTEL-001",
        check_in_date="2026-12-10",
        check_out_date="2026-12-13",
        guests=4,
        rooms=2,
    )

    assert request.guests == 4
    assert request.rooms == 2
    assert request.check_in_date.isoformat() == "2026-12-10"



def test_checkout_before_checkin():
    with pytest.raises(ValidationError):
        HotelAvailabilityRequest(
            hotel_id="HOTEL-001",
            guests=4,
            check_in_date="2026-12-13",
            check_out_date="2026-12-10",
            rooms=2,
        )


def test_invalid_room_count():
    with pytest.raises(ValidationError):
        HotelAvailabilityRequest(
            hotel_id="HOTEL-001",
            guests=4,
            check_in_date="2026-12-10",
            check_out_date="2026-12-13",
            rooms=0,
        )


def test_invalid_date():
    with pytest.raises(ValidationError):
        HotelAvailabilityRequest(
            hotel_id="HOTEL-001",
            guests=4,
            check_in_date="2026-02-30",
            check_out_date="2026-03-03",
            rooms=1,
        )
