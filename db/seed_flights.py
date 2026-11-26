from db.models.inventory import Flight
from db.session import SessionLocal
from db.models.availability import FlightAvailability

FLIGHTS = [
    {
        "flight_id": "FLT-001",
        "airline": "Saudi Skies",
        "origin": "Riyadh",
        "destination": "Jeddah",
        "departure_date": "2026-12-20",
        "departure_time": "08:00",
        "arrival_time": "10:00",
        "duration_minutes": 120,
        "price_sar": 420.0,
        "cabin": "economy",
        "direct": True,
        "baggage_kg": 23,
    },
    {
        "flight_id": "FLT-002",
        "airline": "Saudi Skies",
        "origin": "Riyadh",
        "destination": "Jeddah",
        "departure_date": "2026-12-20",
        "departure_time": "18:30",
        "arrival_time": "20:30",
        "duration_minutes": 120,
        "price_sar": 360.0,
        "cabin": "economy",
        "direct": True,
        "baggage_kg": 23,
    },
    {
        "flight_id": "FLT-003",
        "airline": "Gulf Wings",
        "origin": "Riyadh",
        "destination": "Dammam",
        "departure_date": "2026-12-20",
        "departure_time": "09:15",
        "arrival_time": "10:20",
        "duration_minutes": 65,
        "price_sar": 280.0,
        "cabin": "economy",
        "direct": True,
        "baggage_kg": 23,
    },
    {
        "flight_id": "FLT-004",
        "airline": "Saudi Skies",
        "origin": "Dammam",
        "destination": "Riyadh",
        "departure_date": "2026-12-20",
        "departure_time": "14:00",
        "arrival_time": "15:10",
        "duration_minutes": 70,
        "price_sar": 290.0,
        "cabin": "economy",
        "direct": True,
        "baggage_kg": 23,
    },
    {
        "flight_id": "FLT-005",
        "airline": "Desert Air",
        "origin": "Riyadh",
        "destination": "Dubai",
        "departure_date": "2026-12-20",
        "departure_time": "07:30",
        "arrival_time": "10:00",
        "duration_minutes": 150,
        "price_sar": 650.0,
        "cabin": "economy",
        "direct": True,
        "baggage_kg": 23,
    },
    {
        "flight_id": "FLT-006",
        "airline": "Gulf Wings",
        "origin": "Riyadh",
        "destination": "Dubai",
        "departure_date": "2026-12-20",
        "departure_time": "16:00",
        "arrival_time": "18:30",
        "duration_minutes": 150,
        "price_sar": 580.0,
        "cabin": "economy",
        "direct": True,
        "baggage_kg": 23,
    },
    {
        "flight_id": "FLT-007",
        "airline": "Saudi Skies",
        "origin": "Jeddah",
        "destination": "Riyadh",
        "departure_date": "2026-12-20",
        "departure_time": "11:00",
        "arrival_time": "13:00",
        "duration_minutes": 120,
        "price_sar": 400.0,
        "cabin": "economy",
        "direct": True,
        "baggage_kg": 23,
    },
    {
        "flight_id": "FLT-008",
        "airline": "Desert Air",
        "origin": "Jeddah",
        "destination": "Dubai",
        "departure_date": "2026-12-20",
        "departure_time": "09:45",
        "arrival_time": "12:15",
        "duration_minutes": 150,
        "price_sar": 620.0,
        "cabin": "economy",
        "direct": True,
        "baggage_kg": 23,
    },
    {
        "flight_id": "FLT-009",
        "airline": "Saudi Skies",
        "origin": "Riyadh",
        "destination": "Jeddah",
        "departure_date": "2026-12-20",
        "departure_time": "21:00",
        "arrival_time": "23:00",
        "duration_minutes": 120,
        "price_sar": 900.0,
        "cabin": "business",
        "direct": True,
        "baggage_kg": 23,
    },
]


def seed_flights() -> None:
    with SessionLocal() as session:
        for data in FLIGHTS:
            existing = (
                session.query(Flight)
                .filter_by(flight_id=data["flight_id"])
                .first()
            )

            if existing is None:
                session.add(Flight(**data))
            else:
                # Synchronize only the date for existing
                # synthetic flights.
                existing.departure_date = data["departure_date"]

        session.commit()

    print(f"Synchronized {len(FLIGHTS)} synthetic flights.")


def seed_flight_availability() -> None:
    with SessionLocal() as session:
        flights = session.query(Flight).all()

        created = 0

        for flight in flights:
            existing = (
                session.query(FlightAvailability)
                .filter_by(flight_id=flight.id)
                .first()
            )

            if existing is not None:
                continue

            availability = FlightAvailability(
                flight_id=flight.id,
                available_seats=20,
            )

            session.add(availability)
            created += 1

        session.commit()

    print(f"Created {created} flight availability records.")


if __name__ == "__main__":
    seed_flights()
    seed_flight_availability()
