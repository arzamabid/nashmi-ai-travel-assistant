from datetime import date

from pydantic import BaseModel, Field, model_validator


class HotelAvailabilityRequest(BaseModel):
    hotel_id: str = Field(min_length=1)
    check_in_date: date
    check_out_date: date
    guests: int = Field(gt=0)
    rooms: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.check_out_date <= self.check_in_date:
            raise ValueError(
                "Check-out must be after check-in."
            )
        return self



class HotelAvailabilityResult(BaseModel):
    hotel_id: str
    check_in_date: str
    check_out_date: str
    guests: int
    rooms: int
    available: bool
