"""Read-only, localhost-only DEMO booking history.

No production identity is inferred from the browser's user_id parameter.
This endpoint is OFF unless explicitly enabled for local development.
"""
import json
import os
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from db.models.base import Booking, BookingItem, User
from db.models.inventory import Flight, Hotel, Restaurant
from db.session import SessionLocal

router = APIRouter(tags=["Demo booking history"])


def query_confirmed_bookings(session, user_key="USER-001"):
    """Return saved confirmed items belonging to this server-selected demo user."""
    user = session.scalar(select(User).where(User.user_id == user_key))
    if user is None:
        return []
    rows = session.execute(
        select(Booking, BookingItem)
        .join(BookingItem, BookingItem.booking_id == Booking.id)
        .where(Booking.user_id == user.id, Booking.status == "confirmed")
        .order_by(Booking.created_at.desc(), Booking.id.desc(), BookingItem.id)
    ).all()
    result = []
    for booking, item in rows:
        try:
            details = json.loads(item.details or "{}")
            if not isinstance(details, dict):
                details = {}
        except (ValueError, TypeError):
            details = {}
        label, location, extra = item.item_id, None, {}
        if item.item_type == "restaurant":
            entity = session.scalar(select(Restaurant).where(Restaurant.restaurant_id == item.item_id))
            if entity:
                label, location = entity.name, entity.city
                extra = {"cuisine": entity.cuisine}
        elif item.item_type == "hotel":
            entity = session.scalar(select(Hotel).where(Hotel.hotel_id == item.item_id))
            if entity:
                label, location = entity.name, entity.city
        elif item.item_type == "flight":
            entity = session.scalar(select(Flight).where(Flight.flight_id == item.item_id))
            if entity:
                label, location = entity.airline, f"{entity.origin} → {entity.destination}"
                extra = {"departure_date": entity.departure_date, "departure_time": entity.departure_time}
        result.append({
            "reference": booking.booking_id,
            "status": booking.status,
            "service_type": item.item_type,
            "item_id": item.item_id,
            "name": label,
            "location": location,
            "details": details,
            "extra": extra,
            "created_at": booking.created_at.isoformat() if booking.created_at else None,
        })
    return result


@router.get("/bookings/history")
def get_demo_booking_history(request: Request):
    # Security: this proof-of-concept must never be exposed on a public server.
    if os.getenv("NASHMI_LOCAL_DEMO_BOOKINGS", "0") != "1":
        raise HTTPException(status_code=403, detail="Booking history requires authentication; local demo access is disabled")
    if request.client is None or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(status_code=403, detail="Demo history is restricted to localhost")
    with SessionLocal() as session:
        return {"mode": "local_demo", "bookings": query_confirmed_bookings(session)}
