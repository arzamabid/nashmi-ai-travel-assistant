
from pydantic import BaseModel, Field


class RestaurantSearchRequest(BaseModel):
    city: str = Field(min_length=1)
    cuisine: str | None = None

    date: str | None = None
    time: str | None = None

    party_size: int = Field(gt=0)

    max_budget_sar: float | None = Field(
        default=None,
        gt=0,
    )

    family_friendly: bool | None = None


class RestaurantSearchResult(BaseModel):
    restaurant_id: str
    name: str
    city: str
    cuisine: str
    price_level: str
    family_friendly: bool
