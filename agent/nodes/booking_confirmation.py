
import re

from agent.graph.state import NashmiState
from tools.schemas.booking import BookingConfirmationRequest
from tools.booking_tools import (
    cancel_booking_preview,
    confirm_flight_booking,
    confirm_hotel_booking,
    confirm_restaurant_booking,
)


def normalize_booking_message(message: str) -> str:
    """Normalize user wording for safe phrase matching."""
    message = message.strip().lower()

    # Remove Arabic diacritics and tatweel.
    message = re.sub(
        r"[\u0640\u064b-\u065f\u0670]",
        "",
        message,
    )

    # Normalize common Arabic letter variants.
    message = re.sub(r"[إأآٱ]", "ا", message)

    # Normalize punctuation and whitespace.
    message = re.sub(r"[،,؟?!؛.]", " ", message)
    message = re.sub(r"\s+", " ", message)

    return message.strip()


def booking_response(
    language: str,
    kind: str,
    service_type: str = "",
    booking_id: str = "",
    item_id: str = "",
) -> str:
    if language == "ar":
        service_names = {
            "flight": "الرحلة",
            "hotel": "الفندق",
            "restaurant": "المطعم",
        }

        service = service_names.get(
            service_type, "الخدمة"
        )

        messages = {
            "confirmed": (
                f"تم تأكيد حجز {service} بنجاح. "
                f"رقم الحجز: {booking_id}. "
                f"المرجع: {item_id}."
            ),
            "cancelled": (
                "تم إلغاء طلب الحجز المبدئي. "
                "لم يتم حجز أي مقاعد أو غرف أو مواعيد. "
                "يمكنك بدء بحث جديد."
            ),
            "approval_required": (
                "لتأكيد الحجز، قل: نعم، أكد الحجز. "
                "أو قل: ألغِ الحجز."
            ),
        }
    else:
        messages = {
            "confirmed": (
                f"Your simulated {service_type} booking "
                f"{booking_id} has been confirmed. "
                f"Reference: {item_id}."
            ),
            "cancelled": (
                "Your pending booking preview has been "
                "cancelled. No inventory was reserved. "
                "You can start a new search."
            ),
            "approval_required": (
                "Please explicitly confirm by saying "
                "'Yes, confirm the booking', "
                "or tell me you want to cancel."
            ),
        }

    return messages[kind]

def confirm_booking_node(state: NashmiState) -> dict:
    message = normalize_booking_message(
        state.get("user_message", "")
    )

    language = state.get("language", "en")
    preview_id = state.get("booking_preview_id")
    user_id = state.get("user_id")
    service_type = state.get("selected_service_type")

    # Confirm only an awaiting booking preview.
    if (
        state.get("status") != "awaiting_booking_confirmation"
        or not preview_id
    ):
        return {
            "status": "booking_confirmation_rejected",
            "user_confirmed": False,
            "response": "There is no pending booking to confirm.",
        }

    # Handle explicit cancellation of a pending preview.

    cancellation_phrases = {
        "cancel",
        "cancel booking",
        "cancel the booking",
        "cancel my booking",
        "no cancel",
        "no cancel it",
        "no cancel the booking",
        "don't book",
        "do not book",
        "الغ الحجز",
        "الغاء الحجز",
        "لا الغ الحجز",
        "لا اريد الحجز",
        "لا تحجز",
    }

    if message in cancellation_phrases:
        if not user_id:
            return {
                "status": "booking_cancellation_failed",
                "user_confirmed": False,
                "response": "A valid user account is required.",
            }

        try:
            cancel_booking_preview(
                preview_id=preview_id,
                user_id=user_id,
            )
        except ValueError as error:
            return {
                "status": "booking_cancellation_failed",
                "user_confirmed": False,
                "response": str(error),
            }

        return {
            "status": "booking_preview_cancelled",
            "booking_preview_id": "",
            "selected_item_id": "",
            "selected_service_type": "",
            "user_confirmed": False,
            "response": booking_response(
                            language,
                            "cancelled",
                        ),
        }

    # Require explicit booking approval.

    approval_patterns = (
        r"yes\s+confirm(?:\s+(?:(?:the|my|this)\s+)?booking)?",
        r"confirm\s+(?:the|my|this)\s+booking",
        r"proceed\s+with\s+(?:the|my|this)\s+booking",
    )

    arabic_approval_phrases = {
        "نعم اكد الحجز",
        "اكد الحجز",
        "اؤكد الحجز",
        "تاكيد الحجز",
        "نعم اريد تاكيد الحجز",
    }

    approved = (
        message in arabic_approval_phrases
        or any(
            re.fullmatch(pattern, message)
            for pattern in approval_patterns
        )
    )

    if not approved:
        return {
            "status": "awaiting_booking_confirmation",
            "user_confirmed": False,
            "response": booking_response(
                language,
                "approval_required",
            ),
        }

    if not user_id:
        return {
            "status": "booking_confirmation_failed",
            "user_confirmed": False,
            "response": "A valid user account is required.",
        }

    # Select the existing confirmation tool.
    confirmation_tools = {
        "flight": confirm_flight_booking,
        "hotel": confirm_hotel_booking,
        "restaurant": confirm_restaurant_booking,
    }

    confirmation_tool = confirmation_tools.get(service_type)

    if confirmation_tool is None:
        return {
            "status": "booking_confirmation_failed",
            "user_confirmed": False,
            "response": "Unsupported booking service.",
        }

    try:
        result = confirmation_tool(
            BookingConfirmationRequest(
                preview_id=preview_id,
                user_id=user_id,
                confirmed=True,
            )
        )
    except ValueError as error:
        return {
            "status": "booking_confirmation_failed",
            "user_confirmed": False,
            "response": str(error),
        }

    return {
        "status": "booking_confirmed",
        "user_confirmed": True,
        "booking_preview_id": "",
        "response": booking_response(
            language,
            "confirmed",
            service_type=service_type,
            booking_id=result.booking_id,
            item_id=result.item_id,
        ),
    }
