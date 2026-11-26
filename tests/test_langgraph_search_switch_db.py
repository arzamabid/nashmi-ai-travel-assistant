
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import tools.booking_tools as booking_tools
import agent.graph.workflow as workflow

from db.models.base import Booking, BookingItem, User
from db.models.inventory import Flight
from db.models.availability import FlightAvailability


def test_flight_to_hotel_switch(monkeypatch):
    url = os.environ.get("DATABASE_URL", "")

    # Protect the main development database.
    if not url or make_url(url).database != "nashmi_test":
        pytest.skip("Requires isolated nashmi_test database.")

    engine = create_engine(url)
    sessions = sessionmaker(bind=engine)

    monkeypatch.setattr(
        booking_tools, "SessionLocal", sessions
    )

    suffix = uuid4().hex[:10]
    user_key = f"TEST-USER-{suffix}"
    flight_key = f"TEST-FLIGHT-{suffix}"
    preview_id = f"PREVIEW-SWITCH-{suffix}"

    user_pk = None
    flight_pk = None
    booking_pk = None

    # Mock the hotel search stages only.
    # Cancellation itself will use real PostgreSQL.
    def fake_hotel_extraction(state):
        assert state["hotel_request"] == {}

        return {
            "hotel_request": {
                "destination": "Jeddah",
                "check_in_date": "2026-12-20",
                "check_out_date": "2026-12-22",
                "guests": 2,
                "rooms": 1,
            },
            "missing_fields": [],
            "status": "hotel_parameters_extracted",
        }

    def fake_hotel_search(state):
        return {
            "hotel_results": [
                {"hotel_id": "TEST-HOTEL-001"}
            ],
            "status": "hotel_search_completed",
        }

    def fake_hotel_availability(state):
        return {
            "available_hotels": state["hotel_results"],
            "status": "hotel_availability_checked",
        }

    monkeypatch.setattr(
        workflow,
        "extract_hotel_node",
        fake_hotel_extraction,
    )
    monkeypatch.setattr(
        workflow,
        "hotel_node",
        fake_hotel_search,
    )
    monkeypatch.setattr(
        workflow,
        "check_hotel_availability_node",
        fake_hotel_availability,
    )

    try:
        # 1. Create a pending flight preview.
        with sessions.begin() as session:
            user = User(
                user_id=user_key,
                display_name="Search Switch Test",
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

        # 2. Build graph after applying the mocks.
        graph = workflow.build_graph()

        result = graph.invoke(
            {
                "user_id": user_key,
                "user_message": (
                    "No, find me a hotel in Jeddah instead"
                ),
                "intent": "flight_selection",
                "status": "awaiting_booking_confirmation",
                "booking_preview_id": preview_id,
                "selected_service_type": "flight",
                "selected_item_id": flight_key,
                "user_confirmed": False,
                "hotel_request": {
                    "destination": "Riyadh",
                    "rooms": 5,
                },
            },
            config={
                "configurable": {
                    "thread_id": f"switch-{suffix}"
                }
            },
        )

        # 3. Verify LangGraph switched services.
        assert result["status"] == (
            "hotel_availability_checked"
        )
        assert result["intent"] == "hotel_search"
        assert result["booking_preview_id"] == ""
        assert result["selected_item_id"] == ""
        assert result["user_confirmed"] is False

        # Old hotel parameters must not be reused.
        assert result["hotel_request"]["destination"] == "Jeddah"
        assert result["hotel_request"]["rooms"] == 1

        # 4. Verify actual PostgreSQL cancellation.
        with sessions() as session:
            stored_booking = session.get(Booking, booking_pk)

            assert stored_booking.status == "cancelled"

            inventory = session.scalar(
                select(FlightAvailability).where(
                    FlightAvailability.flight_id == flight_pk
                )
            )

            # No seats were reserved.
            assert inventory.available_seats == 5

    finally:
        # 5. Clean up test records.
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
                        delete(User).where(User.id == user_pk
                        )
                    )
        finally:
            engine.dispose()
