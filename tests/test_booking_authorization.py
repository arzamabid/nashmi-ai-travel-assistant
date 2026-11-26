"""Integration test: a different user must not confirm another user's flight.

Run only against an existing, initialized, disposable nashmi_test database.
"""
import json
import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from db.models.base import AuditEvent, Booking, BookingItem, User
from db.models.availability import FlightAvailability
from db.models.inventory import Flight
from tools.schemas.booking import BookingConfirmationRequest
import tools.booking_tools as booking_tools


@pytest.mark.integration
def test_other_user_cannot_confirm_flight_booking(monkeypatch):
    raw_url = os.getenv("DATABASE_URL", "")
    if not raw_url:
        pytest.skip("DATABASE_URL must explicitly select nashmi_test.")

    try:
        parsed = make_url(raw_url)
    except Exception:
        pytest.fail("DATABASE_URL is malformed.")

    if parsed.database != "nashmi_test":
        pytest.skip("Refusing to modify any database except nashmi_test.")

    engine = create_engine(raw_url)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid4().hex[:12]
    owner_key = f"AUTH-OWNER-{suffix}"
    intruder_key = f"AUTH-OTHER-{suffix}"
    flight_key = f"AUTH-FLT-{suffix}"
    preview_key = f"PREVIEW-AUTH-{suffix}"
    user_ids = []
    seeded = False

    try:
        # Verify actual target DB before any data changes.
        with engine.connect() as connection:
            actual_db = connection.execute(text("SELECT current_database()" )).scalar_one()
            assert actual_db == "nashmi_test", "Connected to unexpected database."

        monkeypatch.setattr(booking_tools, "SessionLocal", session_factory)

        with session_factory.begin() as session:
            owner = User(user_id=owner_key, display_name="Authorization Test Owner")
            other = User(user_id=intruder_key, display_name="Authorization Test Other")
            flight = Flight(
                flight_id=flight_key,
                airline="Test Airline",
                origin="RUH",
                destination="JED",
                departure_date="2026-12-20",
                departure_time="10:00",
                arrival_time="11:00",
                duration_minutes=60,
                price_sar=100,
                cabin="economy",
                direct=True,
                baggage_kg=20,
            )
            session.add_all([owner, other, flight])
            session.flush()
            user_ids = [owner.id, other.id]
            session.add(FlightAvailability(flight_id=flight.id, available_seats=3))
            booking = Booking(
                booking_id=preview_key,
                user_id=owner.id,
                service_type="flight",
                status="pending_confirmation",
            )
            session.add(booking)
            session.flush()
            session.add(BookingItem(
                booking_id=booking.id,
                item_type="flight",
                item_id=flight_key,
                details=json.dumps({"passengers": 2}),
            ))
        seeded = True

        with pytest.raises(ValueError, match="Booking belongs to another user"):
            booking_tools.confirm_flight_booking(
                BookingConfirmationRequest(
                    preview_id=preview_key,
                    user_id=intruder_key,
                    confirmed=True,
                )
            )

        with session_factory() as session:
            booking = session.scalar(select(Booking).where(Booking.booking_id == preview_key))
            inventory = session.scalar(
                select(FlightAvailability).join(Flight).where(Flight.flight_id == flight_key)
            )
            audits = session.scalars(select(AuditEvent).where(
                AuditEvent.user_id.in_(user_ids),
                AuditEvent.event_type == "booking_confirmed",
            )).all()
            assert booking is not None and booking.status == "pending_confirmation"
            assert inventory is not None and inventory.available_seats == 3
            assert len(audits) == 0
    finally:
        # Record-scoped cleanup; never truncate or drop tables.
        try:
            if user_ids or seeded:
                with session_factory.begin() as session:
                    for event in session.scalars(
                        select(AuditEvent).where(AuditEvent.user_id.in_(user_ids))
                    ).all():
                        session.delete(event)
                    session.flush()

                    bookings = session.scalars(
                        select(Booking).where(Booking.booking_id == preview_key)
                    ).all()
                    for booking in bookings:
                        for item in session.scalars(
                            select(BookingItem).where(BookingItem.booking_id == booking.id)
                        ).all():
                            session.delete(item)
                    session.flush()
                    for booking in bookings:
                        session.delete(booking)
                    session.flush()

                    inventory = session.scalar(
                        select(FlightAvailability).join(Flight).where(Flight.flight_id == flight_key)
                    )
                    if inventory is not None:
                        session.delete(inventory)
                        session.flush()
                    flight = session.scalar(select(Flight).where(Flight.flight_id == flight_key))
                    if flight is not None:
                        session.delete(flight)
                        session.flush()
                    for user in session.scalars(select(User).where(User.user_id.in_([owner_key, intruder_key]))).all():
                        session.delete(user)
        finally:
            engine.dispose()
