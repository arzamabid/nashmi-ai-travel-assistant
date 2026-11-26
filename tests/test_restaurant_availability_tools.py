
from unittest.mock import MagicMock, patch

from tools.restaurant_availability_tools import (
    check_restaurant_availability,
)
from tools.schemas.restaurant_availability import (
    RestaurantAvailabilityRequest,
)


def test_restaurant_available():
    restaurant = MagicMock()
    restaurant.id = 1

    slot = MagicMock()

    session = MagicMock()
    query = session.query.return_value
    query.filter.return_value = query
    query.first.side_effect = [restaurant, slot]

    context = MagicMock()
    context.__enter__.return_value = session

    request = RestaurantAvailabilityRequest(
        restaurant_id="REST-001",
        date="2026-12-10",
        time="20:00",
        party_size=2,
    )

    with patch(
        "tools.restaurant_availability_tools.SessionLocal",
        return_value=context,
    ):
        result = check_restaurant_availability(request)

    assert result.available is True


def test_restaurant_unavailable_when_slot_missing():
    restaurant = MagicMock()
    restaurant.id = 1

    session = MagicMock()
    query = session.query.return_value
    query.filter.return_value = query
    query.first.side_effect = [restaurant, None]

    context = MagicMock()
    context.__enter__.return_value = session

    request = RestaurantAvailabilityRequest(
        restaurant_id="REST-001",
        date="2026-12-10",
        time="20:00",
        party_size=2,
    )

    with patch(
        "tools.restaurant_availability_tools.SessionLocal",
        return_value=context,
    ):
        result = check_restaurant_availability(request)

    assert result.available is False


def test_restaurant_unavailable_when_unknown():
    session = MagicMock()
    query = session.query.return_value
    query.filter.return_value = query
    query.first.return_value = None

    context = MagicMock()
    context.__enter__.return_value = session

    request = RestaurantAvailabilityRequest(
        restaurant_id="UNKNOWN",
        date="2026-12-10",
        time="20:00",
        party_size=2,
    )

    with patch(
        "tools.restaurant_availability_tools.SessionLocal",
        return_value=context,
    ):
        result = check_restaurant_availability(request)

    assert result.available is False



def test_real_restaurant_availability_postgres():
    from db.models.availability import RestaurantSlot
    from db.models.inventory import Restaurant
    from db.session import SessionLocal

    # Find an existing available restaurant slot.
    # Do not assume today's date was seeded.
    with SessionLocal() as session:
        record = (
            session.query(Restaurant, RestaurantSlot)
            .join(
                RestaurantSlot,
                RestaurantSlot.restaurant_id == Restaurant.id,
            )
            .filter(
                RestaurantSlot.time == "20:00",
                RestaurantSlot.party_size == 4,
                RestaurantSlot.status == "available",
            )
            .order_by(RestaurantSlot.date, RestaurantSlot.id)
            .first()
        )

        assert record is not None, (
            "No available restaurant slot found in test data."
        )

        restaurant, slot = record

        restaurant_id = restaurant.restaurant_id
        slot_date = slot.date
        slot_time = slot.time
        party_size = slot.party_size

    request = RestaurantAvailabilityRequest(
        restaurant_id=restaurant_id,
        date=slot_date,
        time=slot_time,
        party_size=party_size,
    )

    result = check_restaurant_availability(request)

    assert result.restaurant_id == restaurant_id
    assert result.available is True
