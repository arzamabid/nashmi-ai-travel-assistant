from db.models.inventory import Restaurant
from db.session import SessionLocal
from tools.schemas.common import (
    RestaurantSearchRequest,
    RestaurantSearchResult,
)


def search_restaurants(
    request: RestaurantSearchRequest,
) -> list[RestaurantSearchResult]:
    with SessionLocal() as session:
        query = session.query(Restaurant)

        query = query.filter(Restaurant.city.ilike(request.city))

        if request.cuisine:
            query = query.filter(Restaurant.cuisine.ilike(request.cuisine))

        if request.price_level:
            query = query.filter(Restaurant.price_level.ilike(request.price_level))

        if request.family_friendly is not None:
            query = query.filter(Restaurant.family_friendly == request.family_friendly)

        restaurants = query.order_by(Restaurant.name).all()

        return [
            RestaurantSearchResult(
                restaurant_id=restaurant.restaurant_id,
                name=restaurant.name,
                city=restaurant.city,
                cuisine=restaurant.cuisine,
                price_level=restaurant.price_level,
                family_friendly=restaurant.family_friendly,
            )
            for restaurant in restaurants
        ]
