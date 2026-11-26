from db.models.inventory import Hotel
from db.session import SessionLocal
from datetime import date, timedelta

from db.models.availability import HotelAvailability

HOTELS = [
    {
        "hotel_id": "HTL-RYD-001",
        "name": "Riyadh Grand",
        "city": "Riyadh",
        "stars": 5,
        "price_per_night": 850.0,
        "amenities": "wifi,pool,gym,breakfast,parking",
        "family_friendly": True,
    },
    {
        "hotel_id": "HTL-RYD-002",
        "name": "Olaya Suites",
        "city": "Riyadh",
        "stars": 4,
        "price_per_night": 520.0,
        "amenities": "wifi,gym,breakfast,parking",
        "family_friendly": True,
    },
    {
        "hotel_id": "HTL-JED-001",
        "name": "Red Sea Palace",
        "city": "Jeddah",
        "stars": 5,
        "price_per_night": 900.0,
        "amenities": "wifi,pool,gym,breakfast,sea_view,parking",
        "family_friendly": True,
    },
    {
        "hotel_id": "HTL-JED-002",
        "name": "Jeddah Corniche Hotel",
        "city": "Jeddah",
        "stars": 4,
        "price_per_night": 600.0,
        "amenities": "wifi,pool,breakfast,parking",
        "family_friendly": True,
    },
    {
        "hotel_id": "HTL-DMM-001",
        "name": "Dammam Bay Hotel",
        "city": "Dammam",
        "stars": 4,
        "price_per_night": 480.0,
        "amenities": "wifi,pool,gym,breakfast,parking",
        "family_friendly": True,
    },
    {
        "hotel_id": "HTL-KHB-001",
        "name": "Khobar Business Hotel",
        "city": "Al Khobar",
        "stars": 5,
        "price_per_night": 780.0,
        "amenities": "wifi,gym,breakfast,parking,business_center",
        "family_friendly": True,
    },
    {
        "hotel_id": "HTL-MAK-001",
        "name": "Makkah Central Hotel",
        "city": "Makkah",
        "stars": 5,
        "price_per_night": 1100.0,
        "amenities": "wifi,breakfast,shuttle,parking",
        "family_friendly": True,
    },
    {
        "hotel_id": "HTL-MAK-002",
        "name": "Makkah Budget Stay",
        "city": "Makkah",
        "stars": 3,
        "price_per_night": 300.0,
        "amenities": "wifi,parking",
        "family_friendly": True,
    },
    {
        "hotel_id": "HTL-MED-001",
        "name": "Madinah Garden Hotel",
        "city": "Madinah",
        "stars": 4,
        "price_per_night": 550.0,
        "amenities": "wifi,breakfast,parking,shuttle",
        "family_friendly": True,
    },
]


def seed_hotels() -> None:
    with SessionLocal() as session:
        for data in HOTELS:
            existing = session.query(Hotel).filter_by(hotel_id=data["hotel_id"]).first()

            if existing is None:
                session.add(Hotel(**data))

        session.commit()

    print(f"Seeded {len(HOTELS)} synthetic hotels.")


def seed_hotel_availability() -> None:
    start_date = date(2026, 12, 10)
    number_of_days = 30

    with SessionLocal() as session:
        hotels = session.query(Hotel).all()
        created = 0

        for hotel in hotels:
            for day in range(number_of_days):
                current_date = (
                    start_date + timedelta(days=day)
                ).isoformat()

                existing = (
                    session.query(HotelAvailability)
                    .filter_by(
                        hotel_id=hotel.id,
                        date=current_date,
                    )
                    .first()
                )

                if existing is not None:
                    continue

                availability = HotelAvailability(
                    hotel_id=hotel.id,
                    date=current_date,
                    available_rooms=5,
                )

                session.add(availability)
                created += 1

        session.commit()

    print(f"Seeded {created} hotel availability records.")


if __name__ == "__main__":
    seed_hotels()
    seed_hotel_availability()
