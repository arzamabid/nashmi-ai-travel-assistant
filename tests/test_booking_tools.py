
import pytest

from tools.booking_tools import create_booking_preview
from tools.schemas.booking import BookingPreviewRequest


HOTEL_DETAILS = {
    "check_in_date": "2026-12-20",
    "check_out_date": "2026-12-22",
    "guests": 2,
    "rooms": 1,
}


def test_create_hotel_booking_preview():
    request = BookingPreviewRequest(
        user_id="USER-001",
        service_type="hotel",
        item_id="HTL-RYD-001",
        details=HOTEL_DETAILS,
    )

    result = create_booking_preview(request)

    assert result.preview_id.startswith("PREVIEW-")
    assert result.user_id == "USER-001"
    assert result.service_type == "hotel"
    assert result.item_id == "HTL-RYD-001"
    assert result.details == HOTEL_DETAILS
    assert result.status == "pending_confirmation"
    assert result.requires_confirmation is True


def test_booking_preview_rejects_unknown_user():
    request = BookingPreviewRequest(
        user_id="UNKNOWN",
        service_type="hotel",
        item_id="HTL-RYD-001",
        details=HOTEL_DETAILS,
    )

    with pytest.raises(ValueError, match="Unknown user"):
        create_booking_preview(request)


def test_booking_preview_rejects_unknown_item():
    request = BookingPreviewRequest(
        user_id="USER-001",
        service_type="hotel",
        item_id="UNKNOWN",
        details=HOTEL_DETAILS,
    )

    with pytest.raises(ValueError, match="Unknown hotel"):
        create_booking_preview(request)
