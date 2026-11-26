from pydantic import BaseModel, Field


class FlightSearchRequest(BaseModel):
    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    departure_date: str = Field(min_length=1)
    passengers: int = Field(gt=0)
    cabin: str | None = None
    direct_only: bool | None = None


class FlightSearchResult(BaseModel):
    flight_id: str
    airline: str
    origin: str
    destination: str
    departure_date: str
    departure_time: str
    arrival_time: str
    duration_minutes: int
    cabin: str
    price_sar: float
    baggage_kg: int
    direct: bool
