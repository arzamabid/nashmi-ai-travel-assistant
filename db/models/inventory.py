from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100), index=True)
    cuisine: Mapped[str] = mapped_column(String(100))
    price_level: Mapped[str] = mapped_column(String(50))

    family_friendly: Mapped[bool] = mapped_column(Boolean, default=True)


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    airline: Mapped[str] = mapped_column(String(100))
    origin: Mapped[str] = mapped_column(String(100), index=True)
    destination: Mapped[str] = mapped_column(String(100), index=True)

    departure_date: Mapped[str] = mapped_column(String(20), index=True)
    departure_time: Mapped[str] = mapped_column(String(50))
    arrival_time: Mapped[str] = mapped_column(String(50))

    duration_minutes: Mapped[int] = mapped_column(Integer)

    price_sar: Mapped[float] = mapped_column(Float)
    cabin: Mapped[str] = mapped_column(String(50))

    direct: Mapped[bool] = mapped_column(Boolean, default=True)
    baggage_kg: Mapped[int] = mapped_column(Integer)

class Hotel(Base):
    __tablename__ = "hotels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hotel_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100), index=True)

    stars: Mapped[int] = mapped_column(Integer)
    price_per_night: Mapped[float] = mapped_column(Float)

    amenities: Mapped[str] = mapped_column(String(500))
    family_friendly: Mapped[bool] = mapped_column(Boolean, default=True)
