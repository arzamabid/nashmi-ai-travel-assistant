"""NASHMI Day 4: repeat-confirmation smoke test against EXISTING confirmed demo bookings.

Run from the NASHMI project root:
    python test_nashmi_repeat_confirmations.py

No previews are created, and no pending bookings are confirmed. Only already-
confirmed reservations are selected. The test also checks database inventory
and booking counts before and after. Run only against your LOCAL DEMO database.
"""
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import func

from db.models.base import Booking, BookingItem, User
from db.models.availability import FlightAvailability, HotelAvailability, RestaurantSlot
from db.session import SessionLocal
from tools.booking_tools import (
    confirm_flight_booking,
    confirm_hotel_booking,
    confirm_restaurant_booking,
)
from tools.schemas.booking import BookingConfirmationRequest

TOOLS = {
    "flight": confirm_flight_booking,
    "hotel": confirm_hotel_booking,
    "restaurant": confirm_restaurant_booking,
}


def snapshot():
    """Capture every inventory unit plus booking/item counts to detect mutations."""
    with SessionLocal() as session:
        return {
            "bookings": session.query(func.count(Booking.id)).scalar(),
            "items": session.query(func.count(BookingItem.id)).scalar(),
            "flight_seats": tuple(sorted(
                (row.id, row.available_seats)
                for row in session.query(FlightAvailability).all()
            )),
            "hotel_rooms": tuple(sorted(
                (row.id, row.available_rooms)
                for row in session.query(HotelAvailability).all()
            )),
            "restaurant_slots": tuple(sorted(
                (row.id, row.status)
                for row in session.query(RestaurantSlot).all()
            )),
        }


def existing_confirmed_cases():
    with SessionLocal() as session:
        results = []
        for service in TOOLS:
            booking = (
                session.query(Booking)
                .filter(Booking.service_type == service, Booking.status == "confirmed")
                .order_by(Booking.id.desc())
                .first()
            )
            if booking is None:
                print(f"SKIP {service}: no confirmed demo reservation")
                continue
            user = session.query(User).filter(User.id == booking.user_id).one()
            item_count = (
                session.query(func.count(BookingItem.id))
                .filter(BookingItem.booking_id == booking.id)
                .scalar()
            )
            assert item_count == 1, f"{booking.booking_id}: expected 1 booking item, got {item_count}"
            results.append((service, user.user_id, booking.booking_id))
        return results


def repeat_confirmation(case):
    service, user_id, preview_id = case
    request = BookingConfirmationRequest(
        user_id=user_id,
        preview_id=preview_id,
        confirmed=True,
    )
    result = TOOLS[service](request)
    assert result.booking_id == preview_id, f"Wrong booking returned for {service}"
    assert result.status == "confirmed", f"Unexpected status: {result.status}"
    assert result.confirmed is True
    return result


def main():
    cases = existing_confirmed_cases()
    if not cases:
        raise SystemExit("No confirmed demo reservations: test not run")

    before = snapshot()
    try:
        for case in cases:
            repeat_confirmation(case)
            repeat_confirmation(case)
            print(f"PASS {case[0]}: two sequential repeat confirmations")

            # Parallel repeated confirmations of an ALREADY confirmed booking.
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(repeat_confirmation, [case, case]))
            assert len(results) == 2
            print(f"PASS {case[0]}: two concurrent repeat confirmations")
    finally:
        after = snapshot()
        assert after == before, (
            "FAIL: database counts or inventory changed during repeat confirmation. "
            "Inspect the changes before rerunning."
        )
        print("PASS: booking counts and all inventory unchanged")

    print("PASS: repeat confirmations are idempotent for existing confirmed bookings")
    print("NOTE: simultaneous FIRST confirmation of a pending preview is not tested here.")


if __name__ == "__main__":
    main()
