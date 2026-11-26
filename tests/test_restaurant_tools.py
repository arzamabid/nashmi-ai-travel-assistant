
from db.models.inventory import Restaurant
from db.session import SessionLocal
from tools.restaurant_availability_tools import check_restaurant_availability
from tools.restaurant_tools import search_restaurants
from tools.schemas.common import RestaurantSearchRequest
from tools.schemas.restaurant_availability import RestaurantAvailabilityRequest


def test_restaurant_search_returns_results():
    request = RestaurantSearchRequest(city="Riyadh")

    results = search_restaurants(request)

    assert results
    assert all(result.city == "Riyadh" for result in results)



def test_restaurant_availability_returns_true_for_seeded_slot():
    from db.models.availability import RestaurantSlot

    with SessionLocal() as session:
        record = (
            session.query(Restaurant, RestaurantSlot)
            .join(
                RestaurantSlot,
                RestaurantSlot.restaurant_id == Restaurant.id,
            )
            .filter(RestaurantSlot.status == "available")
            .order_by(RestaurantSlot.date, RestaurantSlot.id)
            .first()
        )

        assert record is not None, "No seeded available slot found."

        restaurant, slot = record

        request = RestaurantAvailabilityRequest(
            restaurant_id=restaurant.restaurant_id,
            date=slot.date,
            time=slot.time,
            party_size=slot.party_size,
        )

    result = check_restaurant_availability(request)

    assert result.restaurant_id == request.restaurant_id
    assert result.available is True


def test_restaurant_availability_returns_false_for_unseeded_party_size():
    from db.models.availability import RestaurantSlot

    with SessionLocal() as session:
        record = (
            session.query(Restaurant, RestaurantSlot)
            .join(
                RestaurantSlot,
                RestaurantSlot.restaurant_id == Restaurant.id,
            )
            .order_by(RestaurantSlot.date, RestaurantSlot.id)
            .first()
        )

        assert record is not None, "No restaurant slots found."

        restaurant, slot = record

        # Choose a party size with no matching slot
        # for this restaurant, date, and time.
        existing_sizes = {
            size
            for (size,) in (
                session.query(RestaurantSlot.party_size)
                .filter(
                    RestaurantSlot.restaurant_id == restaurant.id,
                    RestaurantSlot.date == slot.date,
                    RestaurantSlot.time == slot.time,
                )
                .all()
            )
        }

        unseeded_size = 1
        while unseeded_size in existing_sizes:
            unseeded_size += 1

        request = RestaurantAvailabilityRequest(
            restaurant_id=restaurant.restaurant_id,
            date=slot.date,
            time=slot.time,
            party_size=unseeded_size,
        )

    result = check_restaurant_availability(request)

    assert result.available is False
