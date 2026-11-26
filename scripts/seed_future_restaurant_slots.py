"""Opt-in demo-only future restaurant availability creation.

Preview first; --apply writes to local NASHMI PostgreSQL. No real reservations.
Does not modify existing slots or bookings.
"""
import argparse
from datetime import date, timedelta

from sqlalchemy import select
from db.models.availability import RestaurantSlot
from db.models.inventory import Restaurant
from db.session import SessionLocal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.days <= 60:
        parser.error("days must be between 1 and 60")
    today = date.today()
    end = today + timedelta(days=args.days - 1)
    with SessionLocal() as session:
        restaurants = session.execute(select(Restaurant)).scalars().all()
        existing = session.execute(
            select(RestaurantSlot.restaurant_id, RestaurantSlot.date, RestaurantSlot.time, RestaurantSlot.party_size)
            .where(RestaurantSlot.date >= today.isoformat(), RestaurantSlot.date <= end.isoformat())
        ).all()
        keys = set(existing)
        new = []
        for restaurant in restaurants:
            for offset in range(args.days):
                day = (today + timedelta(days=offset)).isoformat()
                for time in ("18:00", "19:00", "20:00", "21:00"):
                    for party in (2, 4, 6):
                        key = (restaurant.id, day, time, party)
                        if key not in keys:
                            new.append(RestaurantSlot(restaurant_id=restaurant.id, date=day, time=time, party_size=party, status="available"))
                            keys.add(key)
        print(f"Demo restaurants: {len(restaurants)}; existing slots in range: {len(existing)}; proposed new demo slots: {len(new)}")
        if args.apply:
            session.add_all(new)
            session.commit()
            print(f"Added {len(new)} demo-only slots. Existing records preserved.")
        else:
            print("DRY RUN ONLY. To write new demo slots, rerun with --apply.")


if __name__ == "__main__":
    main()
