"""Safe unit tests for flight confirmation validation.

These tests mock SessionLocal and never connect to PostgreSQL.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools.booking_tools import confirm_flight_booking
from tools.schemas.booking import BookingConfirmationRequest


def _request():
    return BookingConfirmationRequest(
        preview_id="PREVIEW-VALIDATION-TEST",
        user_id="TEST-USER",
        confirmed=True,
    )


def _mock_session(*, passengers=2, service_type="flight", item_type="flight", status="pending_confirmation", missing_item=False):
    """Return an isolated mock session with valid user, booking, item and flight."""
    user = MagicMock()
    user.id = 42

    booking = MagicMock()
    booking.id = 99
    booking.user_id = user.id
    booking.booking_id = "PREVIEW-VALIDATION-TEST"
    booking.service_type = service_type
    booking.status = status

    item = MagicMock()
    item.item_type = item_type
    item.item_id = "TEST-FLIGHT"
    item.details = json.dumps({"passengers": passengers})

    flight = MagicMock()
    flight.id = 77

    session = MagicMock()
    session.query.return_value.filter.return_value.first.side_effect = [
        user,
        None if missing_item else item,
        flight,
    ]
    session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = booking
    return session, booking


@pytest.mark.parametrize("passengers", [0, -1, True, "2", None])
def test_invalid_passenger_counts_do_not_modify_inventory(passengers):
    session, booking = _mock_session(passengers=passengers)
    with patch("tools.booking_tools.SessionLocal") as db:
        db.begin.return_value.__enter__.return_value = session
        with pytest.raises(ValueError, match="Invalid passenger count"):
            confirm_flight_booking(_request())
    assert booking.status == "pending_confirmation"
    session.execute.assert_not_called()
    session.add.assert_not_called()


@pytest.mark.parametrize("service_type", ["hotel", "restaurant"])
def test_wrong_booking_service_does_not_modify_inventory(service_type):
    session, booking = _mock_session(service_type=service_type)
    with patch("tools.booking_tools.SessionLocal") as db:
        db.begin.return_value.__enter__.return_value = session
        with pytest.raises(ValueError, match="This function confirms flights only"):
            confirm_flight_booking(_request())
    assert booking.status == "pending_confirmation"
    session.execute.assert_not_called()
    session.add.assert_not_called()


def test_wrong_booking_item_type_does_not_modify_inventory():
    session, booking = _mock_session(item_type="hotel")
    with patch("tools.booking_tools.SessionLocal") as db:
        db.begin.return_value.__enter__.return_value = session
        with pytest.raises(ValueError, match="Invalid booking item type"):
            confirm_flight_booking(_request())
    assert booking.status == "pending_confirmation"
    session.execute.assert_not_called()
    session.add.assert_not_called()


def test_missing_booking_item_does_not_modify_inventory():
    session, booking = _mock_session(missing_item=True)
    with patch("tools.booking_tools.SessionLocal") as db:
        db.begin.return_value.__enter__.return_value = session
        with pytest.raises(ValueError, match="Booking item not found"):
            confirm_flight_booking(_request())
    assert booking.status == "pending_confirmation"
    session.execute.assert_not_called()
    session.add.assert_not_called()


def test_cancelled_booking_cannot_be_confirmed_again():
    session, booking = _mock_session(status="cancelled")
    with patch("tools.booking_tools.SessionLocal") as db:
        db.begin.return_value.__enter__.return_value = session
        with pytest.raises(ValueError, match="Cannot confirm booking with status"):
            confirm_flight_booking(_request())
    assert booking.status == "cancelled"
    session.execute.assert_not_called()
    session.add.assert_not_called()
