
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import tools.booking_tools as booking_tools
from agent.graph.workflow import build_graph
from db.models.base import Booking, BookingItem, User
from db.models.inventory import Hotel, Restaurant
from db.models.availability import (
    HotelAvailability,
    RestaurantSlot,
)


@pytest.mark.parametrize("service", ["hotel", "restaurant"])
def test_service_booking_with_database(monkeypatch, service):
    url = os.environ.get("DATABASE_URL", "")

    # Never run against the main NASHMI database.
    if not url or make_url(url).database != "nashmi_test":
        pytest.skip("Requires isolated nashmi_test database.")

    engine = create_engine(url)
    sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(booking_tools, "SessionLocal", sessions)

    suffix = uuid4().hex[:10]
    user_key = f"TEST-USER-{suffix}"
    item_key = f"TEST-{service.upper()}-{suffix}"

    user_pk = None
    item_pk = None
    preview_id = None

    if service == "hotel":
        details = {
            "check_in_date": "2026-12-20",
            "check_out_date": "2026-12-22",
            "guests": 2,
            "rooms": 1,
        }
        results_key = "available_hotels"
        request_key = "hotel_request"
        id_key = "hotel_id"
    else:
        details = {
            "date": "2026-12-20",
            "time": "19:00",
            "party_size": 2,
        }
        results_key = "available_restaurants"
        request_key = "restaurant_request"
        id_key = "restaurant_id"

    try:
        # Create test records.
        with sessions.begin() as session:
            user = User(
                user_id=user_key,
                display_name="LangGraph DB Test",
            )
            session.add(user)
            session.flush()
            user_pk = user.id

            if service == "hotel":
                item = Hotel(
                    hotel_id=item_key,
                    name="Test Hotel",
                    city="Riyadh",
                    stars=4,
                    price_per_night=300,
                    amenities="WiFi",
                    family_friendly=True,
                )
            else:
                item = Restaurant(
                    restaurant_id=item_key,
                    name="Test Restaurant",
                    city="Riyadh",
                    cuisine="Saudi",
                    price_level="medium",
                    family_friendly=True,
                )

            session.add(item)
            session.flush()
            item_pk = item.id

            if service == "hotel":
                for night in ["2026-12-20", "2026-12-21"]:
                    session.add(
                        HotelAvailability(
                            hotel_id=item_pk,
                            date=night,
                            available_rooms=3,
                        )
                    )
            else:
                session.add(
                    RestaurantSlot(
                        restaurant_id=item_pk,
                        date="2026-12-20",
                        time="19:00",
                        party_size=2,
                        status="available",
                    )
                )

        graph = build_graph()
        config = {
            "configurable": {
                "thread_id": f"service-db-{suffix}"
            }
        }

        # Turn 1: Select the available option.
        first = graph.invoke(
            {
                "user_id": user_key,
                "user_message": "the first one",
                "intent": f"{service}_search",
                "status": f"{service}_availability_checked",
                results_key: [{id_key: item_key}],
                request_key: details,
            },
            config=config,
        )

        assert first["status"] == "awaiting_booking_confirmation"
        assert first["selected_item_id"] == item_key
        assert first["selected_service_type"] == service

        preview_id = first["booking_preview_id"]

        # Preview must not consume inventory.
        with sessions() as session:
            if service == "hotel":
                rows = session.scalars(
                    select(HotelAvailability)
                    .where(HotelAvailability.hotel_id == item_pk)
                    .order_by(HotelAvailability.date)
                ).all()

                assert [r.available_rooms for r in rows] == [3, 3]
            else:
                slot = session.scalar(
                    select(RestaurantSlot).where(
                        RestaurantSlot.restaurant_id == item_pk
                    )
                )
                assert slot.status == "available"

        # Turn 2: Explicit confirmation.
        second = graph.invoke(
            {"user_message": "Yes, confirm the booking"},
            config=config,
        )

        assert second["status"] == "booking_confirmed"
        assert second["user_confirmed"] is True
        assert second["booking_preview_id"] == ""

        # Verify PostgreSQL changes.
        with sessions() as session:
            booking = session.scalar(
                select(Booking).where(
                    Booking.booking_id == preview_id
                )
            )

            assert booking is not None
            assert booking.status == "confirmed"
            assert booking.service_type == service

            if service == "hotel":
                rows = session.scalars(
                    select(HotelAvailability)
                    .where(HotelAvailability.hotel_id == item_pk)
                    .order_by(HotelAvailability.date)
                ).all()

                assert [r.available_rooms for r in rows] == [2, 2]
            else:
                slot = session.scalar(
                    select(RestaurantSlot).where(
                        RestaurantSlot.restaurant_id == item_pk
                    )
                )

                assert slot.status == "booked"

    finally:
        # Delete child records before parent records.
        try:
            with sessions.begin() as session:
                if preview_id:
                    booking = session.scalar(
                        select(Booking).where(
                            Booking.booking_id == preview_id
                        )
                    )

                    if booking is not None:
                        session.execute(
                            delete(BookingItem).where(
                                BookingItem.booking_id == booking.id
                            )
                        )
                        session.execute(
                            delete(Booking).where(
                                Booking.id == booking.id
                            )
                        )

                if item_pk is not None:
                    if service == "hotel":
                        session.execute(
                            delete(HotelAvailability).where(
                                HotelAvailability.hotel_id == item_pk
                            )
                        )
                        session.execute(
                            delete(Hotel).where(Hotel.id == item_pk)
                        )
                    else:
                        session.execute(
                            delete(RestaurantSlot).where(
                                RestaurantSlot.restaurant_id == item_pk
                            )
                        )
                        session.execute(
                            delete(Restaurant).where(
                                Restaurant.id == item_pk
                            )
                        )

                if user_pk is not None:
                    session.execute(
                        delete(User).where(User.id == user_pk)
                    )
        finally:
            engine.dispose()
