from datetime import UTC, datetime, timedelta

from db.models.availability import RestaurantSlot
from db.models.inventory import Restaurant
from db.session import SessionLocal


def seed_restaurant_slots() -> None:
    with SessionLocal() as session:
        restaurants = session.query(Restaurant).all()

        if not restaurants:
            print("No restaurants found. Seed restaurants first.")
            return

        existing_slots = {
            (slot.restaurant_id, slot.date, slot.time, slot.party_size)
            for slot in session.query(RestaurantSlot).all()
        }

        slots = []

        for restaurant in restaurants:
            for day_offset in range(3):
                slot_date = datetime.now(UTC).date() + timedelta(days=day_offset)

                for time in ["18:00", "19:00", "20:00", "21:00"]:
                    for party_size in [2, 4, 6]:
                        if (
                                restaurant.id,
                                slot_date.isoformat(),
                                time,
                                party_size,
                        ) in existing_slots:
                            continue

                        slots.append(
                            RestaurantSlot(
                                restaurant_id=restaurant.id,
                                date=slot_date.isoformat(),
                                time=time,
                                party_size=party_size,
                                status="available",
                            )
                        )

        session.add_all(slots)
        session.commit()

        print(f"Created {len(slots)} restaurant availability slots.")


if __name__ == "__main__":
    seed_restaurant_slots()
