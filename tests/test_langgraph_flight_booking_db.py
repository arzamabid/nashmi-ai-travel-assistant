
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from agent.graph.workflow import build_graph
from db.models.base import Booking, BookingItem, User
from db.models.inventory import Flight
from db.models.availability import FlightAvailability


def test_langgraph_flight_booking_database(monkeypatch):
    url = os.environ.get("DATABASE_URL", "")

    if not url or make_url(url).database != "nashmi_test":
        pytest.skip("Requires nashmi_test database.")

    engine = create_engine(url)
    sessions = sessionmaker(bind=engine)

    import tools.booking_tools as booking_tools
    monkeypatch.setattr(
        booking_tools, "SessionLocal", sessions
    )

    suffix = uuid4().hex[:10]
    user_key = f"TEST-USER-{suffix}"
    flight_key = f"TEST-FLIGHT-{suffix}"

    user_pk = None
    flight_pk = None
    preview_id = None

    try:
        # Create isolated test data.
        with sessions.begin() as session:
            user = User(
                user_id=user_key,
                display_name="LangGraph Test User",
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

        graph = build_graph()
        config = {
            "configurable": {
                "thread_id": f"db-test-{suffix}"
            }
        }

        # Turn 1: Select available flight.
        first = graph.invoke(
            {
                "user_id": user_key,
                "user_message": "the first one",
                "intent": "flight_search",
                "status": "flight_availability_checked",
                "flight_request": {"passengers": 2},
                "available_flights": [
                    {"flight_id": flight_key}
                ],
            },
            config=config,
        )

        assert first["status"] == (
            "awaiting_booking_confirmation"
        )

        preview_id = first["booking_preview_id"]

        # Preview must not deduct inventory.
        with sessions() as session:
            inventory = session.scalar(
                select(FlightAvailability).where(
                    FlightAvailability.flight_id
                    == flight_pk
                )
            )

            assert inventory.available_seats == 5

        # Turn 2: Explicit confirmation.
        second = graph.invoke(
            {
                "user_message": "Yes, confirm the booking",
            },
            config=config,
        )

        assert second["status"] == "booking_confirmed"

        # Check PostgreSQL state.
        with sessions() as session:
            booking = session.scalar(
                select(Booking).where(
                    Booking.booking_id == preview_id
                )
            )

            inventory = session.scalar(
                select(FlightAvailability).where(
                    FlightAvailability.flight_id
                    == flight_pk
                )
            )

            assert booking.status == "confirmed"
            assert inventory.available_seats == 3

    finally:
        # Remove only records created by this test.
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
                                BookingItem.booking_id
                                == booking.id
                            )
                        )
                        session.delete(booking)
                        session.flush()

                if flight_pk is not None:
                    session.execute(
                        delete(FlightAvailability).where(
                            FlightAvailability.flight_id
                            == flight_pk
                        )
                    )
                    session.execute(
                        delete(Flight).where(
                            Flight.id == flight_pk
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
