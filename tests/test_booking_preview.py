
import pytest

from tools.booking_tools import create_booking_preview
from tools.schemas.booking import BookingPreviewRequest


def test_available_flight_preview():
    result = create_booking_preview(
        BookingPreviewRequest(
            user_id="USER-001",
            service_type="flight",
            item_id="FLT-005",
            details={"passengers": 2},
        )
    )

    assert result.status == "pending_confirmation"
    assert result.requires_confirmation is True
    assert result.details["passengers"] == 2
    assert result.preview_id.startswith("PREVIEW-")


def test_insufficient_flight_seats():
    with pytest.raises(ValueError, match="unavailable"):
        create_booking_preview(
            BookingPreviewRequest(
                user_id="USER-001",
                service_type="flight",
                item_id="FLT-005",
                details={"passengers": 999},
            )
        )


def test_unknown_flight():
    with pytest.raises(ValueError, match="Unknown flight"):
        create_booking_preview(
            BookingPreviewRequest(
                user_id="USER-001",
                service_type="flight",
                item_id="FLT-NOT-FOUND",
                details={"passengers": 2},
            )
        )


def test_missing_passengers():
    with pytest.raises(ValueError, match="Missing booking details"):
        BookingPreviewRequest(
            user_id="USER-001",
            service_type="flight",
            item_id="FLT-005",
            details={},
        )
