from db.models.availability import RestaurantSlot
from db.models.inventory import Restaurant
from db.session import SessionLocal
from tools.schemas.restaurant_availability import (
    RestaurantAvailabilityRequest,
    RestaurantAvailabilityResult,
)


def check_restaurant_availability(
    request: RestaurantAvailabilityRequest,
) -> RestaurantAvailabilityResult:
    with SessionLocal() as session:
        restaurant = (
            session.query(Restaurant)
            .filter(Restaurant.restaurant_id == request.restaurant_id)
            .first()
        )

        if restaurant is None:
            return RestaurantAvailabilityResult(
                restaurant_id=request.restaurant_id,
                date=request.date,
                time=request.time,
                party_size=request.party_size,
                available=False,
            )

        slot = (
            session.query(RestaurantSlot)
            .filter(
                RestaurantSlot.restaurant_id == restaurant.id,
                RestaurantSlot.date == request.date,
                RestaurantSlot.time == request.time,
                RestaurantSlot.party_size == request.party_size,
                RestaurantSlot.status == "available",
            )
            .first()
        )

        return RestaurantAvailabilityResult(
            restaurant_id=request.restaurant_id,
            date=request.date,
            time=request.time,
            party_size=request.party_size,
            available=slot is not None,
        )
