from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    home_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), default="Asia/Riyadh")

    preferences: Mapped["Preference | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Preference(Base):
    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)

    cuisines: Mapped[str | None] = mapped_column(Text, nullable=True)
    dietary_preferences: Mapped[str | None] = mapped_column(Text, nullable=True)
    restaurant_price_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    family_friendly: Mapped[bool] = mapped_column(Boolean, default=False)

    preferred_airlines: Mapped[str | None] = mapped_column(Text, nullable=True)
    cabin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hotel_stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hotel_amenities: Mapped[str | None] = mapped_column(Text, nullable=True)

    direct_flight_preference: Mapped[bool] = mapped_column(Boolean, default=False)
    travel_pace: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notification_preference: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    confirmation_policy: Mapped[str] = mapped_column(
        String(50),
        default="always_confirm",
    )
    response_style: Mapped[str] = mapped_column(
        String(50),
        default="concise",
    )

    user: Mapped["User"] = relationship(back_populates="preferences")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    status: Mapped[str] = mapped_column(String(50))
    service_type: Mapped[str] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class BookingItem(Base):
    __tablename__ = "booking_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"))

    item_type: Mapped[str] = mapped_column(String(50))
    item_id: Mapped[str] = mapped_column(String(100))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"))

    status: Mapped[str] = mapped_column(String(50))
    idempotency_key: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(String(100))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
