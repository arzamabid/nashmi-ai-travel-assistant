from pydantic import BaseModel, Field


class RestaurantSearchRequest(BaseModel):
    city: str = Field(min_length=1)
    cuisine: str | None = None
    price_level: str | None = None
    family_friendly: bool | None = None


class RestaurantSearchResult(BaseModel):
    restaurant_id: str
    name: str
    city: str
    cuisine: str
    price_level: str
    family_friendly: bool
