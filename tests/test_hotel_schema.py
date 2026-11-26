
import pytest
from pydantic import ValidationError

from tools.schemas.hotel import HotelSearchRequest


def valid_hotel_data():
    return {
        "destination": "Jeddah",
        "check_in_date": "2026-12-10",
        "check_out_date": "2026-12-12",
        "guests": 2,
        "rooms": 1,
        "stars": 5,
    }


def test_valid_hotel_request():
    request = HotelSearchRequest(**valid_hotel_data())

    assert request.destination == "Jeddah"
    assert request.guests == 2
    assert request.stars == 5


def test_invalid_stars():
    data = valid_hotel_data()
    data["stars"] = 7

    with pytest.raises(ValidationError):
        HotelSearchRequest(**data)


def test_invalid_guests():
    data = valid_hotel_data()
    data["guests"] = -2

    with pytest.raises(ValidationError):
        HotelSearchRequest(**data)


def test_invalid_rooms():
    data = valid_hotel_data()
    data["rooms"] = 0

    with pytest.raises(ValidationError):
        HotelSearchRequest(**data)


def test_empty_destination():
    data = valid_hotel_data()
    data["destination"] = ""

    with pytest.raises(ValidationError):
        HotelSearchRequest(**data)
