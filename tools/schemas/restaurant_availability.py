from pydantic import BaseModel, Field


class RestaurantAvailabilityRequest(BaseModel):
    restaurant_id: str = Field(min_length=1)
    date: str = Field(min_length=1)
    time: str = Field(min_length=1)
    party_size: int = Field(gt=0)


class RestaurantAvailabilityResult(BaseModel):
    restaurant_id: str
    date: str
    time: str
    party_size: int
    available: bool
