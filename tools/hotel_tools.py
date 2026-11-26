from tools.schemas.hotel import (
    HotelSearchRequest,
    HotelSearchResult,
)
from db.models.inventory import Hotel
from db.session import SessionLocal


def search_hotels(
    request: HotelSearchRequest,
) -> list[HotelSearchResult]:
    with SessionLocal() as session:
        query = session.query(Hotel)

        query = query.filter(
            Hotel.city.ilike(request.destination),
        )

        if request.stars is not None:
            query = query.filter(Hotel.stars == request.stars)

        if request.max_budget_sar is not None:
            query = query.filter(
                Hotel.price_per_night <= request.max_budget_sar
            )

        hotels = query.order_by(Hotel.price_per_night).all()

        results = []

        for hotel in hotels:
            hotel_amenities = [
                amenity.strip()
                for amenity in hotel.amenities.split(",")
                if amenity.strip()
            ]

            if request.amenities:
                requested = {
                    amenity.lower()
                    for amenity in request.amenities
                }

                available = {
                    amenity.lower()
                    for amenity in hotel_amenities
                }

                if not requested.issubset(available):
                    continue

            results.append(
                HotelSearchResult(
                    hotel_id=hotel.hotel_id,
                    name=hotel.name,
                    city=hotel.city,
                    stars=hotel.stars,
                    price_per_night_sar=hotel.price_per_night,
                    amenities=hotel_amenities,
                )
            )

        return results