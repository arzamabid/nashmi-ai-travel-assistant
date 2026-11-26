from db.models.inventory import Restaurant
from db.session import SessionLocal

RESTAURANTS = [
    {
        "restaurant_id": "REST-RYD-001",
        "name": "Najd Table",
        "city": "Riyadh",
        "cuisine": "Saudi",
        "price_level": "mid",
        "family_friendly": True,
    },
    {
        "restaurant_id": "REST-RYD-002",
        "name": "Desert Spice",
        "city": "Riyadh",
        "cuisine": "Arabic",
        "price_level": "premium",
        "family_friendly": True,
    },
    {
        "restaurant_id": "REST-RYD-003",
        "name": "Tokyo Riyadh",
        "city": "Riyadh",
        "cuisine": "Japanese",
        "price_level": "premium",
        "family_friendly": True,
    },
    {
        "restaurant_id": "REST-JED-001",
        "name": "Red Sea Kitchen",
        "city": "Jeddah",
        "cuisine": "Seafood",
        "price_level": "mid",
        "family_friendly": True,
    },
    {
        "restaurant_id": "REST-JED-002",
        "name": "Hijazi House",
        "city": "Jeddah",
        "cuisine": "Saudi",
        "price_level": "budget",
        "family_friendly": True,
    },
    {
        "restaurant_id": "REST-DMM-001",
        "name": "Gulf Grill",
        "city": "Dammam",
        "cuisine": "Arabic",
        "price_level": "mid",
        "family_friendly": True,
    },
    {
        "restaurant_id": "REST-KHB-001",
        "name": "Khobar Kitchen",
        "city": "Al Khobar",
        "cuisine": "International",
        "price_level": "mid",
        "family_friendly": True,
    },
    {
        "restaurant_id": "REST-MAK-001",
        "name": "Makkah Table",
        "city": "Makkah",
        "cuisine": "Saudi",
        "price_level": "budget",
        "family_friendly": True,
    },
    {
        "restaurant_id": "REST-MED-001",
        "name": "Madinah Garden",
        "city": "Madinah",
        "cuisine": "Arabic",
        "price_level": "mid",
        "family_friendly": True,
    },
]


def seed_restaurants() -> None:
    with SessionLocal() as session:
        for data in RESTAURANTS:
            existing = (
                session.query(Restaurant).filter_by(restaurant_id=data["restaurant_id"]).first()
            )

            if existing is None:
                session.add(Restaurant(**data))

        session.commit()

    print(f"Seeded {len(RESTAURANTS)} synthetic restaurants.")


if __name__ == "__main__":
    seed_restaurants()
