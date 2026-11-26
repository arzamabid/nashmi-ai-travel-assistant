from db.models.base import Preference, User
from db.session import SessionLocal

USERS = [
    {
        "user": {
            "user_id": "USER-001",
            "display_name": "Ahmed",
            "preferred_language": "ar",
            "home_city": "Riyadh",
            "timezone": "Asia/Riyadh",
        },
        "preference": {
            "cuisines": "Saudi,Japanese",
            "dietary_preferences": "halal",
            "restaurant_price_level": "mid",
            "family_friendly": True,
            "preferred_airlines": "Saudi Skies",
            "cabin": "economy",
            "hotel_stars": 4,
            "hotel_amenities": "wifi,breakfast,parking",
            "direct_flight_preference": True,
            "travel_pace": "balanced",
            "notification_preference": "whatsapp",
            "confirmation_policy": "always_confirm",
            "response_style": "concise",
        },
    },
    {
        "user": {
            "user_id": "USER-002",
            "display_name": "Sara",
            "preferred_language": "en",
            "home_city": "Jeddah",
            "timezone": "Asia/Riyadh",
        },
        "preference": {
            "cuisines": "Seafood,Arabic",
            "dietary_preferences": "halal",
            "restaurant_price_level": "budget",
            "family_friendly": True,
            "preferred_airlines": "Gulf Wings",
            "cabin": "economy",
            "hotel_stars": 3,
            "hotel_amenities": "wifi,parking",
            "direct_flight_preference": True,
            "travel_pace": "relaxed",
            "notification_preference": "email",
            "confirmation_policy": "always_confirm",
            "response_style": "concise",
        },
    },
    {
        "user": {
            "user_id": "USER-003",
            "display_name": "Omar",
            "preferred_language": "en",
            "home_city": "Dammam",
            "timezone": "Asia/Riyadh",
        },
        "preference": {
            "cuisines": "International",
            "dietary_preferences": "halal",
            "restaurant_price_level": "premium",
            "family_friendly": False,
            "preferred_airlines": "Saudi Skies",
            "cabin": "business",
            "hotel_stars": 5,
            "hotel_amenities": "wifi,gym,business_center",
            "direct_flight_preference": True,
            "travel_pace": "fast",
            "notification_preference": "email",
            "confirmation_policy": "always_confirm",
            "response_style": "detailed",
        },
    },
]


def seed_users() -> None:
    with SessionLocal() as session:
        for item in USERS:
            user_data = item["user"]
            preference_data = item["preference"]

            existing_user = session.query(User).filter_by(user_id=user_data["user_id"]).first()

            if existing_user is not None:
                continue

            user = User(**user_data)
            user.preferences = Preference(**preference_data)

            session.add(user)

        session.commit()

    print(f"Seeded {len(USERS)} synthetic users with preferences.")


if __name__ == "__main__":
    seed_users()
