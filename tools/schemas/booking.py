
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BookingPreviewRequest(BaseModel):
    user_id: str = Field(min_length=1)
    service_type: Literal["hotel", "restaurant", "flight"]
    item_id: str = Field(min_length=1)
    details: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_details(self):
        required_fields = {
            "hotel": [
                "check_in_date",
                "check_out_date",
                "guests",
                "rooms",
            ],
            "restaurant": [
                "date",
                "time",
                "party_size",
            ],
            "flight": [
                "passengers",
            ],
        }

        missing = [
            field
            for field in required_fields[self.service_type]
            if self.details.get(field) is None
        ]

        if missing:
            raise ValueError(
                f"Missing booking details: {', '.join(missing)}"
            )

        return self


class BookingPreviewResult(BaseModel):
    preview_id: str
    user_id: str
    service_type: str
    item_id: str
    details: dict
    status: str
    requires_confirmation: bool


class BookingConfirmationRequest(BaseModel):
    preview_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    confirmed: bool


class BookingConfirmationResult(BaseModel):
    booking_id: str
    service_type: str
    item_id: str
    status: str
    confirmed: bool
