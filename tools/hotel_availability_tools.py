
from datetime import timedelta

from db.models.availability import HotelAvailability
from db.models.inventory import Hotel
from db.session import SessionLocal

from tools.schemas.hotel_availability import (
    HotelAvailabilityRequest,
    HotelAvailabilityResult,
)


def check_hotel_availability(
    request: HotelAvailabilityRequest,
) -> HotelAvailabilityResult:

    with SessionLocal() as session:
        hotel = (
            session.query(Hotel)
            .filter(Hotel.hotel_id == request.hotel_id)
            .first()
        )

        if hotel is None:
            available = False

        else:
            available = True
            current_date = request.check_in_date

            while current_date < request.check_out_date:
                inventory = (
                    session.query(HotelAvailability)
                    .filter(
                        HotelAvailability.hotel_id == hotel.id,
                        HotelAvailability.date
                        == current_date.isoformat(),
                    )
                    .first()
                )

                if (
                    inventory is None
                    or inventory.available_rooms < request.rooms
                ):
                    available = False
                    break

                current_date += timedelta(days=1)

    return HotelAvailabilityResult(
        hotel_id=request.hotel_id,
        check_in_date=request.check_in_date.isoformat(),
        check_out_date=request.check_out_date.isoformat(),
        guests=request.guests,
        rooms=request.rooms,
        available=available,
    )
