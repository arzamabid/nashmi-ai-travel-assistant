from uuid import uuid4
import json
from sqlalchemy import update
from datetime import date, timedelta


from db.models.base import User, Booking, BookingItem, AuditEvent
from db.models.inventory import Flight, Hotel, Restaurant
from db.session import SessionLocal
from db.models.availability import FlightAvailability, HotelAvailability, RestaurantSlot
from tools.schemas.booking import (
    BookingPreviewRequest,
    BookingPreviewResult,
    BookingConfirmationRequest,
    BookingConfirmationResult,
)
from tools.hotel_availability_tools import check_hotel_availability
from tools.restaurant_availability_tools import check_restaurant_availability
from tools.flight_availability_tools import check_flight_availability

from tools.schemas.hotel_availability import HotelAvailabilityRequest
from tools.schemas.restaurant_availability import RestaurantAvailabilityRequest
from tools.schemas.flight_availability import FlightAvailabilityRequest



def create_booking_preview(
    request: BookingPreviewRequest,
) -> BookingPreviewResult:
    with SessionLocal() as session:
        user = (
            session.query(User)
            .filter(User.user_id == request.user_id)
            .first()
        )

        if user is None:
            raise ValueError(f"Unknown user: {request.user_id}")

        if request.service_type.lower() == "restaurant":
            item = (
                session.query(Restaurant)
                .filter(Restaurant.restaurant_id == request.item_id)
                .first()
            )
        elif request.service_type.lower() == "flight":
            item = (
                session.query(Flight)
                .filter(Flight.flight_id == request.item_id)
                .first()
            )
        elif request.service_type.lower() == "hotel":
            item = (
                session.query(Hotel)
                .filter(Hotel.hotel_id == request.item_id)
                .first()
            )
        else:
            raise ValueError(
                f"Unsupported service type: {request.service_type}"
            )

        if item is None:
            raise ValueError(
                f"Unknown {request.service_type}: {request.item_id}"
            )

        if request.service_type == "hotel":
            availability_request = HotelAvailabilityRequest(
                hotel_id=request.item_id,
                **request.details,
            )
            availability = check_hotel_availability(
                availability_request
            )

        elif request.service_type == "restaurant":
            availability_request = RestaurantAvailabilityRequest(
                restaurant_id=request.item_id,
                **request.details,
            )
            availability = check_restaurant_availability(
                availability_request
            )

        else:
            availability_request = FlightAvailabilityRequest(
                flight_id=request.item_id,
                **request.details,
            )
            availability = check_flight_availability(
                availability_request
            )

        if not availability.available:
            raise ValueError(
                f"{request.service_type.capitalize()} "
                f"{request.item_id} is unavailable "
                "for the requested booking details."
            )

        preview_id = f"PREVIEW-{uuid4().hex[:8].upper()}"

        booking = Booking(
            booking_id=preview_id,
            user_id=user.id,
            service_type=request.service_type.lower(),
            status="pending_confirmation",
        )

        session.add(booking)
        session.flush()

        booking_item = BookingItem(
            booking_id=booking.id,
            item_type=request.service_type.lower(),
            item_id=request.item_id,
            details=json.dumps(request.details),
        )

        session.add(booking_item)

        # Record the event in the same database transaction
        # as the booking preview.
        session.add(
            AuditEvent(
                user_id=user.id,
                event_type="booking_preview_created",
                details=json.dumps({
                    "booking_id": preview_id,
                    "service_type": request.service_type.lower(),
                    "item_id": request.item_id,
                }),
            )
        )

        session.commit()

        return BookingPreviewResult(
            preview_id=preview_id,
            user_id=request.user_id,
            details=request.details,
            service_type=request.service_type.lower(),
            item_id=request.item_id,
            status="pending_confirmation",
            requires_confirmation=True,
        )


def confirm_flight_booking(
    request: BookingConfirmationRequest,
) -> BookingConfirmationResult:
    if not request.confirmed:
        raise ValueError("Explicit confirmation is required.")

    with SessionLocal.begin() as session:
        user = (
            session.query(User)
            .filter(User.user_id == request.user_id)
            .first()
        )

        if user is None:
            raise ValueError("Unknown user.")

        booking = (
            session.query(Booking)
            .filter(Booking.booking_id == request.preview_id)
            .with_for_update()
            .first()
        )

        if booking is None:
            raise ValueError("Booking preview not found.")

        if booking.user_id != user.id:
            raise ValueError("Booking belongs to another user.")

        if booking.service_type != "flight":
            raise ValueError("This function confirms flights only.")

        item = (
            session.query(BookingItem)
            .filter(BookingItem.booking_id == booking.id)
            .first()
        )

        if item is None:
            raise ValueError("Booking item not found.")

        if item.item_type != "flight":
            raise ValueError("Invalid booking item type.")

        if booking.status == "confirmed":
            return BookingConfirmationResult(
                booking_id=booking.booking_id,
                service_type="flight",
                item_id=item.item_id,
                status="confirmed",
                confirmed=True,
            )

        if booking.status != "pending_confirmation":
            raise ValueError(
                f"Cannot confirm booking with status: {booking.status}"
            )

        details = json.loads(item.details or "{}")
        passengers = details.get("passengers")

        if (
            not isinstance(passengers, int)
            or isinstance(passengers, bool)
            or passengers <= 0
        ):
            raise ValueError("Invalid passenger count.")

        flight = (
            session.query(Flight)
            .filter(Flight.flight_id == item.item_id)
            .first()
        )

        if flight is None:
            raise ValueError("Flight no longer exists.")

        # Atomic inventory deduction:
        # Only succeeds if enough seats remain.
        result = session.execute(
            update(FlightAvailability)
            .where(
                FlightAvailability.flight_id == flight.id,
                FlightAvailability.available_seats >= passengers,
            )
            .values(
                available_seats=(
                    FlightAvailability.available_seats - passengers
                )
            )
        )

        if result.rowcount != 1:
            raise ValueError("Not enough seats available.")

        booking.status = "confirmed"

        session.add(
            AuditEvent(
                user_id=user.id,
                event_type="booking_confirmed",
                details=json.dumps({
                    "booking_id": booking.booking_id,
                    "service_type": "flight",
                    "item_id": item.item_id,
                }),
            )
        )

        return BookingConfirmationResult(
            booking_id=booking.booking_id,
            service_type="flight",
            item_id=item.item_id,
            status="confirmed",
            confirmed=True,
        )


def confirm_hotel_booking(
    request: BookingConfirmationRequest,
) -> BookingConfirmationResult:
    if not request.confirmed:
        raise ValueError("Explicit confirmation is required.")

    with SessionLocal.begin() as session:
        user = (
            session.query(User)
            .filter(User.user_id == request.user_id)
            .first()
        )

        if user is None:
            raise ValueError("Unknown user.")

        booking = (
            session.query(Booking)
            .filter(Booking.booking_id == request.preview_id)
            .with_for_update()
            .first()
        )

        if booking is None:
            raise ValueError("Booking preview not found.")

        if booking.user_id != user.id:
            raise ValueError("Booking belongs to another user.")

        if booking.service_type != "hotel":
            raise ValueError("This function confirms hotels only.")

        item = (
            session.query(BookingItem)
            .filter(BookingItem.booking_id == booking.id)
            .first()
        )

        if item is None or item.item_type != "hotel":
            raise ValueError("Invalid booking item.")

        if booking.status == "confirmed":
            return BookingConfirmationResult(
                booking_id=booking.booking_id,
                service_type="hotel",
                item_id=item.item_id,
                status="confirmed",
                confirmed=True,
            )

        if booking.status != "pending_confirmation":
            raise ValueError(
                f"Cannot confirm booking with status: {booking.status}"
            )

        details = json.loads(item.details or "{}")

        try:
            check_in = date.fromisoformat(details["check_in_date"])
            check_out = date.fromisoformat(details["check_out_date"])
            rooms = details["rooms"]
            guests = details["guests"]
        except (KeyError, TypeError, ValueError):
            raise ValueError("Invalid hotel booking details.")

        if (
            check_out <= check_in
            or not isinstance(rooms, int)
            or isinstance(rooms, bool)
            or rooms <= 0
            or not isinstance(guests, int)
            or isinstance(guests, bool)
            or guests <= 0
        ):
            raise ValueError("Invalid hotel booking details.")

        hotel = (
            session.query(Hotel)
            .filter(Hotel.hotel_id == item.item_id)
            .first()
        )

        if hotel is None:
            raise ValueError("Hotel no longer exists.")

        nights = []
        current_date = check_in

        while current_date < check_out:
            nights.append(current_date.isoformat())
            current_date += timedelta(days=1)

        # Lock all requested nights in a consistent order.
        inventory_rows = (
            session.query(HotelAvailability)
            .filter(
                HotelAvailability.hotel_id == hotel.id,
                HotelAvailability.date.in_(nights),
            )
            .order_by(HotelAvailability.date, HotelAvailability.id)
            .with_for_update()
            .all()
        )

        inventory_by_date = {
            row.date: row for row in inventory_rows
        }

        # Every night must have sufficient rooms.
        for night in nights:
            row = inventory_by_date.get(night)

            if row is None or row.available_rooms < rooms:
                raise ValueError(
                    f"Not enough rooms available for {night}."
                )

        # Deduct all nights within the same transaction.
        for night in nights:
            inventory_by_date[night].available_rooms -= rooms

        booking.status = "confirmed"

        session.add(
            AuditEvent(
                user_id=user.id,
                event_type="booking_confirmed",
                details=json.dumps({
                    "booking_id": booking.booking_id,
                    "service_type": "hotel",
                    "item_id": item.item_id,
                }),
            )
        )

        return BookingConfirmationResult(
            booking_id=booking.booking_id,
            service_type="hotel",
            item_id=item.item_id,
            status="confirmed",
            confirmed=True,
        )



def confirm_restaurant_booking(
    request: BookingConfirmationRequest,
) -> BookingConfirmationResult:
    if not request.confirmed:
        raise ValueError("Explicit confirmation is required.")

    with SessionLocal.begin() as session:
        user = (
            session.query(User)
            .filter(User.user_id == request.user_id)
            .first()
        )

        if user is None:
            raise ValueError("Unknown user.")

        booking = (
            session.query(Booking)
            .filter(Booking.booking_id == request.preview_id)
            .with_for_update()
            .first()
        )

        if booking is None:
            raise ValueError("Booking preview not found.")

        if booking.user_id != user.id:
            raise ValueError("Booking belongs to another user.")

        if booking.service_type != "restaurant":
            raise ValueError(
                "This function confirms restaurants only."
            )

        item = (
            session.query(BookingItem)
            .filter(BookingItem.booking_id == booking.id)
            .first()
        )

        if item is None or item.item_type != "restaurant":
            raise ValueError("Invalid booking item.")

        if booking.status == "confirmed":
            return BookingConfirmationResult(
                booking_id=booking.booking_id,
                service_type="restaurant",
                item_id=item.item_id,
                status="confirmed",
                confirmed=True,
            )

        if booking.status != "pending_confirmation":
            raise ValueError(
                f"Cannot confirm booking with status: {booking.status}"
            )

        details = json.loads(item.details or "{}")

        date_value = details.get("date")
        time_value = details.get("time")
        party_size = details.get("party_size")

        if (
            not isinstance(date_value, str)
            or not date_value
            or not isinstance(time_value, str)
            or not time_value
            or not isinstance(party_size, int)
            or isinstance(party_size, bool)
            or party_size <= 0
        ):
            raise ValueError("Invalid restaurant booking details.")

        restaurant = (
            session.query(Restaurant)
            .filter(
                Restaurant.restaurant_id == item.item_id
            )
            .first()
        )

        if restaurant is None:
            raise ValueError("Restaurant no longer exists.")

        # Lock the matching available slot.
        slot = (
            session.query(RestaurantSlot)
            .filter(
                RestaurantSlot.restaurant_id == restaurant.id,
                RestaurantSlot.date == date_value,
                RestaurantSlot.time == time_value,
                RestaurantSlot.party_size == party_size,
                RestaurantSlot.status == "available",
            )
            .order_by(RestaurantSlot.id)
            .with_for_update()
            .first()
        )

        if slot is None:
            raise ValueError(
                "Restaurant slot is no longer available."
            )

        # Reserve the slot and confirm the booking
        # in the same transaction.
        slot.status = "booked"
        booking.status = "confirmed"

        session.add(
            AuditEvent(
                user_id=user.id,
                event_type="booking_confirmed",
                details=json.dumps({
                    "booking_id": booking.booking_id,
                    "service_type": "restaurant",
                    "item_id": item.item_id,
                }),
            )
        )

        return BookingConfirmationResult(
            booking_id=booking.booking_id,
            service_type="restaurant",
            item_id=item.item_id,
            status="confirmed",
            confirmed=True,
        )



def cancel_booking_preview(
    preview_id: str,
    user_id: str,
) -> str:
    """
    Cancel a pending booking preview.

    Does not cancel an already confirmed booking.
    Does not modify inventory, because previews
    have not reserved any inventory.
    """

    if not preview_id or not user_id:
        raise ValueError("Preview ID and user ID are required.")

    with SessionLocal.begin() as session:
        user = (
            session.query(User)
            .filter(User.user_id == user_id)
            .first()
        )

        if user is None:
            raise ValueError("Unknown user.")

        booking = (
            session.query(Booking)
            .filter(Booking.booking_id == preview_id)
            .with_for_update()
            .first()
        )

        if booking is None:
            raise ValueError("Booking preview not found.")

        if booking.user_id != user.id:
            raise ValueError("Booking belongs to another user.")

        if booking.status == "cancelled":
            return "cancelled"

        if booking.status != "pending_confirmation":
            raise ValueError(
                "Only pending booking previews can be cancelled."
            )

        booking.status = "cancelled"

        session.add(
            AuditEvent(
                user_id=user.id,
                event_type="booking_preview_cancelled",
                details=json.dumps({
                    "booking_id": booking.booking_id,
                    "service_type": booking.service_type,
                }),
            )
        )

        return "cancelled"
