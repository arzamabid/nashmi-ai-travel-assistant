
from unittest.mock import patch

import pytest

from tools.booking_tools import confirm_flight_booking
from tools.schemas.booking import BookingConfirmationRequest


def make_request(confirmed=True, user_id="USER-001"):
    return BookingConfirmationRequest(
        preview_id="PREVIEW-F6BB9B0B",
        user_id=user_id,
        confirmed=confirmed,
    )


def test_explicit_confirmation_required():
    with patch("tools.booking_tools.SessionLocal") as db:
        with pytest.raises(
            ValueError,
            match="Explicit confirmation is required",
        ):
            confirm_flight_booking(make_request(confirmed=False))

        db.begin.assert_not_called()


def test_unknown_user_rejected():
    with patch("tools.booking_tools.SessionLocal") as db:
        session = db.begin.return_value.__enter__.return_value
        session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Unknown user"):
            confirm_flight_booking(make_request())


def test_missing_preview_rejected():
    with patch("tools.booking_tools.SessionLocal") as db:
        session = db.begin.return_value.__enter__.return_value

        user = type("UserStub", (), {"id": 1})()

        session.query.return_value.filter.return_value.first.return_value = user
        session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = None

        with pytest.raises(
            ValueError,
            match="Booking preview not found",
        ):
            confirm_flight_booking(make_request())


def test_insufficient_flight_inventory_rejected():
    from unittest.mock import MagicMock
    from sqlalchemy import update

    from tools.booking_tools import confirm_flight_booking
    from tools.schemas.booking import BookingConfirmationRequest

    request = BookingConfirmationRequest(
        preview_id="PREVIEW-TEST-LOW-SEATS",
        user_id="USER-001",
        confirmed=True,
    )

    with patch("tools.booking_tools.SessionLocal") as db:
        session = db.begin.return_value.__enter__.return_value

        user = MagicMock()
        user.id = 1

        booking = MagicMock()
        booking.id = 10
        booking.user_id = 1
        booking.booking_id = request.preview_id
        booking.service_type = "flight"
        booking.status = "pending_confirmation"

        item = MagicMock()
        item.item_type = "flight"
        item.item_id = "FLT-005"
        item.details = '{"passengers": 5}'

        flight = MagicMock()
        flight.id = 5

        session.query.return_value.filter.return_value.first.side_effect = [
            user,
            item,
            flight,
        ]

        session.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = booking

        session.execute.return_value.rowcount = 0

        with pytest.raises(
            ValueError,
            match="Not enough seats available",
        ):
            confirm_flight_booking(request)

        assert booking.status == "pending_confirmation"
