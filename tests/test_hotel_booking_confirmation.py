
import json
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import tools.booking_tools as booking_tools

from db.models.base import Booking, BookingItem, User
from db.models.inventory import Hotel
from db.models.availability import HotelAvailability
from tools.schemas.booking import BookingConfirmationRequest


def test_hotel_confirmation_and_idempotency(monkeypatch):
    url = os.environ.get("DATABASE_URL", "")

    # Never modify the main NASHMI database.
    if not url or make_url(url).database != "nashmi_test":
        pytest.skip("Requires the isolated nashmi_test database.")

    engine = create_engine(url)
    sessions = sessionmaker(bind=engine)

    monkeypatch.setattr(
        booking_tools,
        "SessionLocal",
        sessions,
    )

    suffix = uuid4().hex[:10]
    user_key = f"TEST-USER-{suffix}"
    hotel_key = f"TEST-HOTEL-{suffix}"
    preview_id = f"PREVIEW-HOTEL-{suffix}"
    failed_preview_id = f"{preview_id}-FAIL"

    user_pk = None
    hotel_pk = None
    booking_pk = None
    failed_booking_pk = None

    try:
        # -----------------------------------------
        # 1. Create test hotel and inventory
        # -----------------------------------------
        with sessions.begin() as session:
            user = User(
                user_id=user_key,
                display_name="Hotel Test User",
            )

            hotel = Hotel(
                hotel_id=hotel_key,
                name="Test Hotel",
                city="Riyadh",
                stars=4,
                price_per_night=300,
                amenities="WiFi",
                family_friendly=True,
            )

            session.add_all([user, hotel])
            session.flush()

            user_pk = user.id
            hotel_pk = hotel.id

            for night in ["2026-12-20", "2026-12-21"]:
                session.add(
                    HotelAvailability(
                        hotel_id=hotel_pk,
                        date=night,
                        available_rooms=3,
                    )
                )

            booking = Booking(
                booking_id=preview_id,
                user_id=user_pk,
                service_type="hotel",
                status="pending_confirmation",
            )

            session.add(booking)
            session.flush()

            booking_pk = booking.id

            session.add(
                BookingItem(
                    booking_id=booking_pk,
                    item_type="hotel",
                    item_id=hotel_key,
                    details=json.dumps({
                        "check_in_date": "2026-12-20",
                        "check_out_date": "2026-12-22",
                        "guests": 2,
                        "rooms": 2,
                    }),
                )
            )

        # -----------------------------------------
        # 2. Confirm hotel booking
        # -----------------------------------------
        request = BookingConfirmationRequest(
            preview_id=preview_id,
            user_id=user_key,
            confirmed=True,
        )

        result = booking_tools.confirm_hotel_booking(request)

        assert result.status == "confirmed"
        assert result.confirmed is True
        assert result.item_id == hotel_key

        # -----------------------------------------
        # 3. Repeat confirmation (idempotency)
        # -----------------------------------------
        second_result = booking_tools.confirm_hotel_booking(
            request
        )

        assert second_result.status == "confirmed"
        assert second_result.confirmed is True

        # -----------------------------------------
        # 4. Verify successful booking inventory
        # -----------------------------------------
        with sessions() as session:
            rows = session.scalars(
                select(HotelAvailability)
                .where(
                    HotelAvailability.hotel_id == hotel_pk
                )
                .order_by(HotelAvailability.date)
            ).all()

            assert len(rows) == 2

            # Three rooms initially, two reserved.
            assert [
                row.available_rooms for row in rows
            ] == [1, 1]

            stored_booking = session.get(
                Booking, booking_pk
            )

            assert stored_booking.status == "confirmed"

        # -----------------------------------------
        # 5. Prepare insufficient-room scenario
        # -----------------------------------------
        with sessions.begin() as session:
            rows = session.scalars(
                select(HotelAvailability)
                .where(
                    HotelAvailability.hotel_id == hotel_pk
                )
                .order_by(HotelAvailability.date)
            ).all()

            # First night has two rooms.
            # Second night has only one room.
            rows[0].available_rooms = 2
            rows[1].available_rooms = 1

            failed_booking = Booking(
                booking_id=failed_preview_id,
                user_id=user_pk,
                service_type="hotel",
                status="pending_confirmation",
            )

            session.add(failed_booking)
            session.flush()

            failed_booking_pk = failed_booking.id

            session.add(
                BookingItem(
                    booking_id=failed_booking_pk,
                    item_type="hotel",
                    item_id=hotel_key,
                    details=json.dumps({
                        "check_in_date": "2026-12-20",
                        "check_out_date": "2026-12-22",
                        "guests": 2,
                        "rooms": 2,
                    }),
                )
            )

        # -----------------------------------------
        # 6. Reject insufficient-room booking
        # -----------------------------------------
        with pytest.raises(
            ValueError,
            match="Not enough rooms available",
        ):
            booking_tools.confirm_hotel_booking(
                BookingConfirmationRequest(
                    preview_id=failed_preview_id,
                    user_id=user_key,
                    confirmed=True,
                )
            )

        # -----------------------------------------
        # 7. Verify no partial inventory deduction
        # -----------------------------------------
        with sessions() as session:
            rows = session.scalars(
                select(HotelAvailability)
                .where(
                    HotelAvailability.hotel_id == hotel_pk
                )
                .order_by(HotelAvailability.date)
            ).all()

            assert [
                row.available_rooms for row in rows
            ] == [2, 1]

            failed_booking = session.get(
                Booking, failed_booking_pk
            )

            assert failed_booking.status == (
                "pending_confirmation"
            )

    finally:
        # -----------------------------------------
        # 8. Clean up test records
        # -----------------------------------------
        try:
            with sessions.begin() as session:

                # Delete booking items before bookings.
                for current_booking_pk in [
                    failed_booking_pk,
                    booking_pk,
                ]:
                    if current_booking_pk is None:
                        continue

                    session.execute(
                        delete(BookingItem).where(
                            BookingItem.booking_id
                            == current_booking_pk
                        )
                    )

                    session.execute(
                        delete(Booking).where(
                            Booking.id == current_booking_pk
                        )
                    )

                # Delete inventory before hotel.
                if hotel_pk is not None:
                    session.execute(
                        delete(HotelAvailability).where(
                            HotelAvailability.hotel_id
                            == hotel_pk
                        )
                    )

                    session.execute(
                        delete(Hotel).where(
                            Hotel.id == hotel_pk
                        )
                    )

                # Delete test user.
                if user_pk is not None:
                    session.execute(
                        delete(User).where(
                            User.id == user_pk
                        )
                    )

        finally:
            engine.dispose()
