from tools.schemas.flight import (
    FlightSearchRequest,
    FlightSearchResult,
)
from db.models.inventory import Flight
from db.session import SessionLocal


def search_flights(
    request: FlightSearchRequest,
) -> list[FlightSearchResult]:
    with SessionLocal() as session:
        query = session.query(Flight)

        query = query.filter(
            Flight.origin.ilike(request.origin),
            Flight.destination.ilike(request.destination),
            Flight.departure_date == request.departure_date,
        )

        if request.cabin:
            query = query.filter(Flight.cabin.ilike(request.cabin))

        if request.direct_only is True:
            query = query.filter(Flight.direct.is_(True))

        flights = query.order_by(Flight.price_sar).all()

        return [
            FlightSearchResult(
                flight_id=flight.flight_id,
                airline=flight.airline,
                origin=flight.origin,
                destination=flight.destination,
                departure_date=flight.departure_date,
                departure_time=flight.departure_time,
                arrival_time=flight.arrival_time,
                duration_minutes=flight.duration_minutes,
                cabin=flight.cabin,
                price_sar=flight.price_sar,
                baggage_kg=flight.baggage_kg,
                direct=flight.direct,
            )
            for flight in flights
        ]
