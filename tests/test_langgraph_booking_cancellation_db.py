
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import tools.booking_tools as booking_tools
from agent.graph.workflow import build_graph
from db.models.base import Booking, BookingItem, User
from db.models.inventory import Flight
from db.models.availability import FlightAvailability


def test_cancel_pending_booking_through_langgraph(monkeypatch):
    url = os.environ.get("DATABASE_URL", "")

    if not url or make_url(url).database != "nashmi_test":
        pytest.skip("Requires isolated nashmi_test database.")

    engine = create_engine(url)
    sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(booking_tools, "SessionLocal", sessions)

    suffix = uuid4().hex[:10]
    user_key = f"TEST-USER-{suffix}"
    flight_key = f"TEST-FLIGHT-{suffix}"
    preview_id = f"PREVIEW-CANCEL-{suffix}"

    user_pk = None
    flight_pk = None
    booking_pk = None

    try:
        # Create one pending booking with 5 available seats.
        with sessions.begin() as session:
            user = User(
                user_id=user_key,
                display_name="Cancellation Test User",
            )

            flight = Flight(
                flight_id=flight_key,
                airline="Test Airline",
                origin="RUH",
                destination="JED",
                departure_date="2026-12-20",
                departure_time="10:00",
                arrival_time="11:00",
                duration_minutes=60,
                price_sar=150,
                cabin="economy",
                direct=True,
                baggage_kg=20,
            )

            session.add_all([user, flight])
            session.flush()

            user_pk = user.id
            flight_pk = flight.id

            session.add(
                FlightAvailability(
                    flight_id=flight_pk,
                    available_seats=5,
                )
            )

            booking = Booking(
                booking_id=preview_id,
                user_id=user_pk,
                service_type="flight",
                status="pending_confirmation",
            )
            session.add(booking)
            session.flush()

            booking_pk = booking.id

            session.add(
                BookingItem(
                    booking_id=booking_pk,
                    item_type="flight",
                    item_id=flight_key,
                    details='{"passengers": 2}',
                )
            )

        graph = build_graph()
        config = {
            "configurable": {
                "thread_id": f"cancel-test-{suffix}"
            }
        }

        # Simulate a conversation awaiting confirmation.
        result = graph.invoke(
            {
                "user_id": user_key,
                "user_message": "No, cancel it",
                "intent": "flight_selection",
                "status": "awaiting_booking_confirmation",
                "booking_preview_id": preview_id,
                "selected_service_type": "flight",
                "selected_item_id": flight_key,
                "user_confirmed": False,
            },
            config=config,
        )

        assert result["status"] == "booking_preview_cancelled"
        assert result["booking_preview_id"] == ""
        assert result["user_confirmed"] is False

        # Verify PostgreSQL was updated.
        with sessions() as session:
            stored_booking = session.get(Booking, booking_pk)

            assert stored_booking.status == "cancelled"

            inventory = session.scalar(
                select(FlightAvailability).where(
                    FlightAvailability.flight_id == flight_pk
                )
            )

            # Cancellation must not deduct any seats.
            assert inventory.available_seats == 5

    finally:
        # Clean up test data in dependency order.
        try:
            with sessions.begin() as session:
                if booking_pk is not None:
                    session.execute(
                        delete(BookingItem).where(
                            BookingItem.booking_id == booking_pk
                        )
                    )
                    session.execute(
                        delete(Booking).where(
                            Booking.id == booking_pk
                        )
                    )

                if flight_pk is not None:
                    session.execute(
                        delete(FlightAvailability).where(
                            FlightAvailability.flight_id == flight_pk
                        )
                    )
                    session.execute(
                        delete(Flight).where(
                            Flight.id == flight_pk
                        )
                    )

                if user_pk is not None:
                    session.execute(
                        delete(User).where(User.id == user_pk)
                    )
        finally:
            engine.dispose()
