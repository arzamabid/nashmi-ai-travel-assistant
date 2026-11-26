from pydantic import BaseModel, Field


class HotelSearchRequest(BaseModel):
    destination: str = Field(min_length=1)
    check_in_date: str = Field(min_length=1)
    check_out_date: str = Field(min_length=1)
    guests: int = Field(gt=0)
    rooms: int = Field(gt=0)
    stars: int | None = Field(default=None, ge=1, le=5)
    amenities: list[str] = Field(default_factory=list)
    max_budget_sar: float | None = Field(default=None, gt=0)


class HotelSearchResult(BaseModel):
    hotel_id: str
    name: str
    city: str
    stars: int
    price_per_night_sar: float
    amenities: list[str]
