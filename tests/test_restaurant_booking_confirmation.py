
import json
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import tools.booking_tools as booking_tools

from db.models.base import Booking, BookingItem, User
from db.models.inventory import Restaurant
from db.models.availability import RestaurantSlot
from tools.schemas.booking import BookingConfirmationRequest


def test_restaurant_confirmation(monkeypatch):
    url = os.environ.get("DATABASE_URL", "")

    # Protect the main development database.
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
    restaurant_key = f"TEST-REST-{suffix}"

    preview_id = f"PREVIEW-REST-{suffix}"
    second_preview_id = f"{preview_id}-SECOND"

    user_pk = None
    restaurant_pk = None
    slot_pk = None
    booking_ids = []

    try:
        # 1. Create isolated restaurant test data.
        with sessions.begin() as session:
            user = User(
                user_id=user_key,
                display_name="Restaurant Test User",
            )

            restaurant = Restaurant(
                restaurant_id=restaurant_key,
                name="Test Restaurant",
                city="Riyadh",
                cuisine="Saudi",
                price_level="medium",
                family_friendly=True,
            )

            session.add_all([user, restaurant])
            session.flush()

            user_pk = user.id
            restaurant_pk = restaurant.id

            slot = RestaurantSlot(
                restaurant_id=restaurant_pk,
                date="2026-12-20",
                time="19:00",
                party_size=2,
                status="available",
            )

            session.add(slot)
            session.flush()

            slot_pk = slot.id

            # Two different bookings request the same slot.
            for current_preview_id in [
                preview_id,
                second_preview_id,
            ]:
                booking = Booking(
                    booking_id=current_preview_id,
                    user_id=user_pk,
                    service_type="restaurant",
                    status="pending_confirmation",
                )

                session.add(booking)
                session.flush()

                booking_ids.append(booking.id)

                session.add(
                    BookingItem(
                        booking_id=booking.id,
                        item_type="restaurant",
                        item_id=restaurant_key,
                        details=json.dumps({
                            "date": "2026-12-20",
                            "time": "19:00",
                            "party_size": 2,
                        }),
                    )
                )

        # 2. Confirm first booking.
        request = BookingConfirmationRequest(
            preview_id=preview_id,
            user_id=user_key,
            confirmed=True,
        )

        result = booking_tools.confirm_restaurant_booking(request)

        assert result.status == "confirmed"
        assert result.confirmed is True
        assert result.item_id == restaurant_key

        # 3. Confirm same booking again.
        repeated_result = (
            booking_tools.confirm_restaurant_booking(request)
        )

        assert repeated_result.status == "confirmed"

        # 4. Try booking the already-reserved slot.
        with pytest.raises(
            ValueError,
            match="Restaurant slot is no longer available",
        ):
            booking_tools.confirm_restaurant_booking(
                BookingConfirmationRequest(
                    preview_id=second_preview_id,
                    user_id=user_key,
                    confirmed=True,
                )
            )

        # 5. Verify database state.
        with sessions() as session:
            stored_slot = session.get(
                RestaurantSlot,
                slot_pk,
            )

            assert stored_slot.status == "booked"

            bookings = session.scalars(
                select(Booking).where(
                    Booking.id.in_(booking_ids)
                )
            ).all()

            status_by_preview = {
                booking.booking_id: booking.status
                for booking in bookings
            }

            assert status_by_preview[preview_id] == "confirmed"

            assert (
                status_by_preview[second_preview_id]
                == "pending_confirmation"
            )

    finally:
        # 6. Remove only records created by this test.
        try:
            with sessions.begin() as session:
                if booking_ids:
                    session.execute(
                        delete(BookingItem).where(
                            BookingItem.booking_id.in_(booking_ids)
                        )
                    )

                    session.execute(
                        delete(Booking).where(
                            Booking.id.in_(booking_ids)
                        )
                    )

                if slot_pk is not None:
                    session.execute(
                        delete(RestaurantSlot).where(
                            RestaurantSlot.id == slot_pk
                        )
                    )

                if restaurant_pk is not None:
                    session.execute(
                        delete(Restaurant).where(
                            Restaurant.id == restaurant_pk
                        )
                    )

                if user_pk is not None:
                    session.execute(
                        delete(User).where(
                            User.id == user_pk
                        )
                    )

        finally:
            engine.dispose()
