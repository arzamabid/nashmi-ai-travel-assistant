from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base


class RestaurantSlot(Base):
    __tablename__ = "restaurant_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id"),
        index=True,
    )

    date: Mapped[str] = mapped_column(String(20), index=True)
    time: Mapped[str] = mapped_column(String(10))
    party_size: Mapped[int] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(
        String(30),
        default="available",
    )


class HotelAvailability(Base):
    __tablename__ = "hotel_availability"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    hotel_id: Mapped[int] = mapped_column(
        ForeignKey("hotels.id"),
        index=True,
    )

    date: Mapped[str] = mapped_column(
        String(20),
        index=True,
    )

    available_rooms: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )


class FlightAvailability(Base):
    __tablename__ = "flight_availability"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    flight_id: Mapped[int] = mapped_column(
        ForeignKey("flights.id"),
        index=True,
    )

    available_seats: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
