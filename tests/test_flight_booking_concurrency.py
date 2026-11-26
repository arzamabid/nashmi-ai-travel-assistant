
import json
import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from db.models.base import (
    AuditEvent,
    Booking,
    BookingItem,
    User,
)
from db.models.inventory import Flight
from db.models.availability import FlightAvailability
from tools.schemas.booking import BookingConfirmationRequest
import tools.booking_tools as booking_tools


@pytest.mark.integration
def test_concurrent_flight_confirmation(monkeypatch):
    """
    Verify that two different booking previews competing
    for the same limited flight inventory cannot both
    succeed.

    Uses only the isolated nashmi_test database.
    """

    database_url = os.environ.get("DATABASE_URL", "")

    if not database_url:
        pytest.skip(
            "DATABASE_URL is not configured for nashmi_test."
        )

    # Hard safety guard: never use the main NASHMI database.
    try:
        parsed_url = make_url(database_url)
    except Exception:
        pytest.skip("Invalid test database URL.")

    if parsed_url.database != "nashmi_test":
        pytest.skip(
            "Concurrency test requires the isolated "
            "nashmi_test database."
        )

    engine = create_engine(database_url)

    test_sessions = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    # Make the booking tool use the isolated test DB.
    monkeypatch.setattr(
        booking_tools,
        "SessionLocal",
        test_sessions,
    )

    suffix = uuid4().hex[:10]

    user_key = f"TEST-USER-{suffix}"
    flight_key = f"TEST-FLT-{suffix}"

    preview_keys = [
        f"PREVIEW-TEST-{suffix}-A",
        f"PREVIEW-TEST-{suffix}-B",
    ]

    test_user_id = None

    try:
        # ====================================================
        # 1. CREATE ISOLATED TEST DATA
        # ====================================================

        with test_sessions.begin() as session:

            user = User(
                user_id=user_key,
                display_name="Concurrency Test",
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
                price_sar=100,
                cabin="economy",
                direct=True,
                baggage_kg=20,
            )

            session.add_all([user, flight])
            session.flush()

            test_user_id = user.id

            # Only two seats are available.
            session.add(
                FlightAvailability(
                    flight_id=flight.id,
                    available_seats=2,
                )
            )

            # Create two independent pending previews.
            # Each requests all two available seats.
            for preview_id in preview_keys:

                booking = Booking(
                    booking_id=preview_id,
                    user_id=user.id,
                    service_type="flight",
                    status="pending_confirmation",
                )

                session.add(booking)
                session.flush()

                session.add(
                    BookingItem(
                        booking_id=booking.id,
                        item_type="flight",
                        item_id=flight_key,
                        details=json.dumps({
                            "passengers": 2,
                        }),
                    )
                )

        # ====================================================
        # 2. EXECUTE CONCURRENT CONFIRMATIONS
        # ====================================================

        def confirm(preview_id):

            try:
                result = booking_tools.confirm_flight_booking(
                    BookingConfirmationRequest(
                        preview_id=preview_id,
                        user_id=user_key,
                        confirmed=True,
                    )
                )

                return result.status

            except ValueError as error:
                return str(error)

        with ThreadPoolExecutor(max_workers=2) as executor:

            outcomes = list(
                executor.map(
                    confirm,
                    preview_keys,
                )
            )

        # Exactly one reservation should succeed.
        assert outcomes.count("confirmed") == 1, outcomes

        # The competing reservation should fail
        # because no seats remain.
        assert sum(
            "Not enough seats available" in outcome
            for outcome in outcomes
        ) == 1, outcomes

        # ====================================================
        # 3. VERIFY DATABASE CONSISTENCY
        # ====================================================

        with test_sessions() as session:

            inventory = session.scalar(
                select(FlightAvailability)
                .join(Flight)
                .where(
                    Flight.flight_id == flight_key
                )
            )

            assert inventory is not None

            # Two available seats minus one booking
            # of two passengers equals zero.
            assert inventory.available_seats == 0

            bookings = session.scalars(
                select(Booking)
                .where(
                    Booking.booking_id.in_(preview_keys)
                )
            ).all()

            assert len(bookings) == 2

            assert sorted(
                booking.status for booking in bookings
            ) == [
                "confirmed",
                "pending_confirmation",
            ]

            # =================================================
            # 4. VERIFY AUDIT-EVENT IDEMPOTENCY
            # =================================================

            audit_events = session.scalars(
                select(AuditEvent)
                .where(
                    AuditEvent.user_id == test_user_id,
                    AuditEvent.event_type == "booking_confirmed",
                )
            ).all()

            # Only the successful confirmation should
            # generate a confirmation audit event.
            assert len(audit_events) == 1

            event_details = json.loads(
                audit_events[0].details or "{}"
            )

            confirmed_booking = next(
                booking
                for booking in bookings
                if booking.status == "confirmed"
            )

            assert event_details["booking_id"] == (
                confirmed_booking.booking_id
            )

            assert event_details["service_type"] == "flight"

            assert event_details["item_id"] == flight_key

    finally:

        # ====================================================
        # 5. CLEAN UP ONLY THIS TEST'S RECORDS
        # ====================================================

        try:
            with test_sessions.begin() as session:

                # Delete audit events first because they
                # reference the temporary test user.
                if test_user_id is not None:

                    audit_events = session.scalars(
                        select(AuditEvent)
                        .where(
                            AuditEvent.user_id == test_user_id
                        )
                    ).all()

                    for event in audit_events:
                        session.delete(event)

                    session.flush()

                # Delete booking items before bookings.
                bookings = session.scalars(
                    select(Booking)
                    .where(
                        Booking.booking_id.in_(preview_keys)
                    )
                ).all()

                booking_ids = [
                    booking.id for booking in bookings
                ]

                if booking_ids:

                    items = session.scalars(
                        select(BookingItem)
                        .where(
                            BookingItem.booking_id.in_(
                                booking_ids
                            )
                        )
                    ).all()

                    for item in items:
                        session.delete(item)

                    session.flush()

                # Delete temporary bookings.
                for booking in bookings:
                    session.delete(booking)

                session.flush()

                # Delete temporary availability.
                inventory = session.scalar(
                    select(FlightAvailability)
                    .join(Flight)
                    .where(
                        Flight.flight_id == flight_key
                    )
                )

                if inventory is not None:
                    session.delete(inventory)
                    session.flush()

                # Delete temporary flight.
                flight = session.scalar(
                    select(Flight)
                    .where(
                        Flight.flight_id == flight_key
                    )
                )

                if flight is not None:
                    session.delete(flight)
                    session.flush()

                # Delete temporary user.
                user = session.scalar(
                    select(User)
                    .where(
                        User.user_id == user_key
                    )
                )

                if user is not None:
                    session.delete(user)

        finally:
            engine.dispose()
