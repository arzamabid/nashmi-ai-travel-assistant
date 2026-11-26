
from pydantic import BaseModel, Field


class FlightAvailabilityRequest(BaseModel):
    flight_id: str = Field(min_length=1)
    passengers: int = Field(gt=0)


class FlightAvailabilityResult(BaseModel):
    flight_id: str
    passengers: int
    available_seats: int
    available: bool
