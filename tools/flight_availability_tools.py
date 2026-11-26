
from db.models.availability import FlightAvailability
from db.models.inventory import Flight
from db.session import SessionLocal

from tools.schemas.flight_availability import (
    FlightAvailabilityRequest,
    FlightAvailabilityResult,
)


def check_flight_availability(
    request: FlightAvailabilityRequest,
) -> FlightAvailabilityResult:

    with SessionLocal() as session:
        flight = (
            session.query(Flight)
            .filter(Flight.flight_id == request.flight_id)
            .first()
        )

        if flight is None:
            available_seats = 0
            available = False

        else:
            inventory = (
                session.query(FlightAvailability)
                .filter(
                    FlightAvailability.flight_id == flight.id
                )
                .first()
            )

            if inventory is None:
                available_seats = 0
                available = False
            else:
                available_seats = inventory.available_seats
                available = (
                    available_seats >= request.passengers
                )

    return FlightAvailabilityResult(
        flight_id=request.flight_id,
        passengers=request.passengers,
        available_seats=available_seats,
        available=available,
    )
