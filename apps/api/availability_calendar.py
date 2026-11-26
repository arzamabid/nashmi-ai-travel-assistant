"""Read-only availability calendar endpoints for NASHMI.

Install as apps/api/availability_calendar.py and include the router in apps/api/main.py.
All availability is local demo inventory, not external supplier availability.
"""
from calendar import monthrange
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from agent.utils.locations import normalize_city
from db.session import engine

router = APIRouter(tags=["Availability calendars"])


def _month_bounds(year: int, month: int):
    if not 2020 <= year <= 2100 or not 1 <= month <= 12:
        raise HTTPException(status_code=422, detail="Invalid calendar month")
    return date(year, month, 1).isoformat(), date(year, month, monthrange(year, month)[1]).isoformat()


def _normal_city(city: str) -> str:
    value = normalize_city(city.strip())
    if not value:
        raise HTTPException(status_code=422, detail="City is required")
    return value


@router.get("/hotels/calendar")
def hotel_calendar(
    city: str = Query(min_length=1, max_length=100),
    year: int = Query(ge=2020, le=2100),
    month: int = Query(ge=1, le=12),
    rooms: int = Query(default=1, ge=1, le=20),
):
    """Dates with at least one hotel having enough rooms for that night.

    A green date is *not* confirmation that an entire multi-night stay is available.
    Use /hotels/stay-check to verify the whole range before searching/book preview.
    """
    first, last = _month_bounds(year, month)
    city = _normal_city(city)
    query = text("""
        SELECT a.date, COUNT(DISTINCT h.id) AS hotel_count,
               MIN(h.price_per_night) AS starting_price
        FROM hotels h JOIN hotel_availability a ON a.hotel_id = h.id
        WHERE LOWER(h.city) = LOWER(:city)
          AND a.date BETWEEN :first AND :last
          AND a.date >= :today
          AND a.available_rooms >= :rooms
        GROUP BY a.date ORDER BY a.date
    """)
    with engine.connect() as db:
        rows = db.execute(query, {"city": city, "first": first, "last": last,
                                  "today": date.today().isoformat(), "rooms": rooms}).mappings().all()
    return {"city": city, "year": year, "month": month, "rooms": rooms,
            "days": [{"date": r["date"], "hotel_count": r["hotel_count"],
                      "starting_price": r["starting_price"]} for r in rows]}


@router.get("/hotels/stay-check")
def hotel_stay_check(
    city: str = Query(min_length=1, max_length=100),
    check_in: date = Query(),
    check_out: date = Query(),
    rooms: int = Query(default=1, ge=1, le=20),
):
    """Only hotels with enough rooms on EVERY night are returned."""
    city = _normal_city(city)
    nights = (check_out - check_in).days
    if check_in < date.today() or not 1 <= nights <= 30:
        raise HTTPException(422, "Check-in must be today or later; stay must be 1–30 nights")
    query = text("""
        SELECT h.hotel_id, h.name, h.price_per_night,
               MIN(a.available_rooms) AS minimum_rooms,
               COUNT(DISTINCT a.date) AS nights_available
        FROM hotels h
        JOIN hotel_availability a ON a.hotel_id = h.id
        WHERE LOWER(h.city) = LOWER(:city)
          AND a.date >= :check_in AND a.date < :check_out
          AND a.available_rooms >= :rooms
        GROUP BY h.id, h.hotel_id, h.name, h.price_per_night
        HAVING COUNT(DISTINCT a.date) = :nights
        ORDER BY h.price_per_night, h.name
    """)
    with engine.connect() as db:
        rows = db.execute(query, {"city": city, "check_in": check_in.isoformat(),
                                  "check_out": check_out.isoformat(), "rooms": rooms,
                                  "nights": nights}).mappings().all()
    return {"city": city, "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(), "rooms": rooms,
            "nights": nights, "hotels": [
                {"hotel_id": r["hotel_id"], "name": r["name"],
                 "price_per_night": r["price_per_night"],
                 "minimum_rooms": r["minimum_rooms"]} for r in rows
            ]}


@router.get("/restaurants/calendar")
def restaurant_calendar(
    city: str = Query(min_length=1, max_length=100),
    year: int = Query(ge=2020, le=2100),
    month: int = Query(ge=1, le=12),
    party_size: int = Query(default=2, ge=1, le=30),
):
    """Available date/time slots for the requested exact party size."""
    first, last = _month_bounds(year, month)
    city = _normal_city(city)
    query = text("""
        SELECT s.date, s.time, COUNT(DISTINCT r.id) AS restaurant_count
        FROM restaurant_slots s
        JOIN restaurants r ON r.id = s.restaurant_id
        WHERE LOWER(r.city) = LOWER(:city)
          AND s.date BETWEEN :first AND :last
          AND s.date >= :today
          AND s.party_size = :party_size
          AND s.status = 'available'
        GROUP BY s.date, s.time
        ORDER BY s.date, s.time
    """)
    with engine.connect() as db:
        rows = db.execute(query, {"city": city, "first": first, "last": last,
                                  "today": date.today().isoformat(),
                                  "party_size": party_size}).mappings().all()
    by_date = {}
    for r in rows:
        by_date.setdefault(r["date"], []).append({
            "time": r["time"], "restaurant_count": r["restaurant_count"]})
    return {"city": city, "year": year, "month": month,
            "party_size": party_size, "days": [
                {"date": day, "slots": slots} for day, slots in by_date.items()
            ]}

@router.get("/hotels/cities")
def hotel_cities():
    """Actual demo hotel cities for the visual hotel planner."""
    with engine.connect() as db:
        rows = db.execute(text("""
            SELECT DISTINCT city FROM hotels
            WHERE TRIM(city) <> '' ORDER BY city
        """)).scalars().all()
    return {"cities": list(rows)}


@router.get("/restaurants/cities")
def restaurant_cities():
    """Cities with actual demo restaurant records."""
    with engine.connect() as db:
        rows = db.execute(text("""
            SELECT DISTINCT city FROM restaurants
            WHERE TRIM(city) <> '' ORDER BY city
        """)).scalars().all()
    return {"cities": list(rows)}


@router.get("/restaurants/browse")
def restaurant_browse(city: str = Query(min_length=1, max_length=100)):
    """Display actual restaurants even when no booking date is provided."""
    city = _normal_city(city)
    with engine.connect() as db:
        rows = db.execute(text("""
            SELECT r.restaurant_id, r.name, r.city, r.cuisine,
                   r.price_level, r.family_friendly,
                   COUNT(s.id) FILTER (
                      WHERE s.status = 'available' AND s.date >= :today
                   ) AS available_slot_count
            FROM restaurants r
            LEFT JOIN restaurant_slots s ON s.restaurant_id = r.id
            WHERE LOWER(r.city) = LOWER(:city)
            GROUP BY r.id, r.restaurant_id, r.name, r.city,
                     r.cuisine, r.price_level, r.family_friendly
            ORDER BY r.name
        """), {"city": city, "today": date.today().isoformat()}).mappings().all()
    return {"city": city, "restaurants": [dict(row) for row in rows]}


@router.get("/flights/routes")
def flight_routes():
    """Distinct demo flight routes from the local flights table; read-only."""
    with engine.connect() as db:
        rows = db.execute(text("""
            SELECT DISTINCT origin, destination FROM flights
            WHERE TRIM(origin) <> '' AND TRIM(destination) <> ''
            ORDER BY origin, destination
        """)).mappings().all()
    return {"routes": [dict(row) for row in rows]}
