
import re
from calendar import monthrange
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from agent.graph.workflow import build_graph
from apps.api.availability_calendar import (
    router as availability_calendar_router,
)
from apps.api.booking_history import (
    router as booking_history_router,
)
from db.session import engine
from tools.hotel_tools import search_hotels
from tools.schemas.hotel import (
    HotelSearchRequest,
    HotelSearchResult,
)
from apps.api.observability import RequestLoggingMiddleware


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="NASHMI API",
    version="0.1.0",
)
app.add_middleware(RequestLoggingMiddleware)
# Hotel, restaurant, and flight discovery/calendar endpoints.
app.include_router(availability_calendar_router)

# Persistent booking-history endpoints.
app.include_router(booking_history_router)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "NASHMI",
    }


# ============================================================
# FLIGHT AVAILABILITY CALENDAR
# ============================================================

@app.get("/flights/calendar")
def flight_calendar(
    origin: str,
    destination: str,
    year: int,
    month: int,
    passengers: int = 1,
):
    if not 1 <= month <= 12:
        raise HTTPException(
            status_code=400,
            detail="Invalid month",
        )

    if not 1 <= passengers <= 20:
        raise HTTPException(
            status_code=400,
            detail="Invalid passenger count",
        )

    if not 2020 <= year <= 2100:
        raise HTTPException(
            status_code=400,
            detail="Invalid year",
        )

    first = date(year, month, 1)

    last = date(
        year,
        month,
        monthrange(year, month)[1],
    )

    query = text("""
        SELECT
            f.departure_date AS date,
            COUNT(*) AS flight_count,
            MIN(f.price_sar) AS starting_price
        FROM flights f
        JOIN flight_availability a
            ON a.flight_id = f.id
        WHERE LOWER(f.origin) = LOWER(:origin)
          AND LOWER(f.destination) = LOWER(:destination)
          AND f.departure_date >= :first_date
          AND f.departure_date <= :last_date
          AND a.available_seats >= :passengers
        GROUP BY f.departure_date
        ORDER BY f.departure_date
    """)

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {
                "origin": origin.strip(),
                "destination": destination.strip(),
                "first_date": first.isoformat(),
                "last_date": last.isoformat(),
                "passengers": passengers,
            },
        ).mappings().all()

    return {
        "origin": origin,
        "destination": destination,
        "year": year,
        "month": month,
        "passengers": passengers,
        "days": [
            {
                "date": row["date"],
                "flight_count": row["flight_count"],
                "starting_price": row["starting_price"],
            }
            for row in rows
        ],
    }


# ============================================================
# HOTEL SEARCH
# ============================================================

@app.post(
    "/hotels/search",
    response_model=list[HotelSearchResult],
)
def hotel_search(request: HotelSearchRequest):
    return search_hotels(request)


# ============================================================
# LANGGRAPH CONVERSATION ENGINE
# ============================================================

# Build the graph once so the in-memory checkpointer
# retains conversation state between API requests.
nashmi_graph = build_graph()


def detect_language(message: str) -> str:
    """Detect Arabic or English from user input."""

    arabic_pattern = r"[\u0600-\u06FF]"

    if re.search(arabic_pattern, message):
        return "ar"

    return "en"


# ============================================================
# CHAT REQUEST / RESPONSE MODELS
# ============================================================

class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)

    # Explicit language selection is optional.
    language: str | None = Field(
        default=None,
        pattern=r"^(en|ar)$",
    )


class ChatResponse(BaseModel):
    session_id: str
    intent: str | None = None
    status: str
    response: str
    language: str

    flight_request: dict = Field(default_factory=dict)
    hotel_request: dict = Field(default_factory=dict)
    restaurant_request: dict = Field(default_factory=dict)

    available_flights: list[dict] = Field(
        default_factory=list
    )
    available_hotels: list[dict] = Field(
        default_factory=list
    )
    available_restaurants: list[dict] = Field(
        default_factory=list
    )

    booking_preview_id: str | None = None


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    # Separate LangGraph conversations by user and session.
    # This identifier is for demo conversation isolation,
    # not production authentication.
    thread_id = (
        f"{request.user_id}:{request.session_id}"
    )

    language = (
        request.language
        or detect_language(request.message)
    )

    result = nashmi_graph.invoke(
        {
            "user_id": request.user_id,
            "session_id": request.session_id,
            "user_message": request.message,
            "language": language,
        },
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

    status = result.get("status", "unknown")

    available_flights = (
        result.get("available_flights") or []
    )

    available_hotels = (
        result.get("available_hotels") or []
    )

    available_restaurants = (
        result.get("available_restaurants") or []
    )

    response_text = result.get("response") or ""

    # --------------------------------------------------------
    # FLIGHT SEARCH RESPONSE
    # --------------------------------------------------------

    if status == "flight_availability_checked":

        if available_flights:
            if language == "en":
                response_text = (
                    f"I found {len(available_flights)} "
                    "available flights. "
                    "Please select an option by number."
                )
            else:
                response_text = (
                    f"وجدت {len(available_flights)} "
                    "رحلات متاحة. "
                    "يرجى اختيار الرحلة برقم الخيار."
                )
        else:
            if language == "en":
                response_text = (
                    "I couldn't find available flights "
                    "matching your search. "
                    "Try different dates or routes."
                )
            else:
                response_text = (
                    "لم أجد رحلات متاحة تطابق طلبك. "
                    "يمكنك تجربة تاريخ أو مسار آخر."
                )

    # --------------------------------------------------------
    # HOTEL SEARCH RESPONSE
    # --------------------------------------------------------

    elif status == "hotel_availability_checked":

        if available_hotels:
            if language == "en":
                response_text = (
                    f"I found {len(available_hotels)} "
                    "available hotels. "
                    "Please select an option by number."
                )
            else:
                response_text = (
                    f"وجدت {len(available_hotels)} "
                    "فنادق متاحة. "
                    "يرجى اختيار الفندق برقم الخيار."
                )
        else:
            if language == "en":
                response_text = (
                    "I couldn't find available hotels "
                    "matching your search. "
                    "Try different dates, fewer rooms, "
                    "or another destination."
                )
            else:
                response_text = (
                    "لم أجد فنادق متاحة تطابق طلبك. "
                    "يمكنك تجربة تواريخ أخرى أو عدد غرف أقل "
                    "أو مدينة أخرى."
                )

    # --------------------------------------------------------
    # RESTAURANT SEARCH RESPONSE
    # --------------------------------------------------------

    elif status == "restaurant_availability_checked":

        if available_restaurants:
            if language == "en":
                response_text = (
                    f"I found {len(available_restaurants)} "
                    "available restaurants. "
                    "Please select an option by number."
                )
            else:
                response_text = (
                    f"وجدت {len(available_restaurants)} "
                    "مطاعم متاحة. "
                    "يرجى اختيار المطعم برقم الخيار."
                )
        else:
            if language == "en":
                response_text = (
                    "I couldn't find available restaurants "
                    "matching your search. "
                    "Try another date or time."
                )
            else:
                response_text = (
                    "لم أجد مطاعم متاحة تطابق طلبك. "
                    "يمكنك تجربة تاريخ أو وقت آخر."
                )

    # --------------------------------------------------------
    # FALLBACK RESPONSE
    # --------------------------------------------------------

    elif not response_text:

        if language == "en":
            response_text = (
                "I couldn't complete that request. "
                "Please provide more details."
            )
        else:
            response_text = (
                "لم أتمكن من إكمال طلبك. "
                "يرجى تقديم مزيد من التفاصيل."
            )

    # --------------------------------------------------------
    # RETURN STRUCTURED RESPONSE
    # --------------------------------------------------------

    return ChatResponse(
        session_id=request.session_id,
        intent=result.get("intent"),
        status=status,
        language=language,
        response=response_text,

        flight_request=(
            result.get("flight_request") or {}
        ),
        hotel_request=(
            result.get("hotel_request") or {}
        ),
        restaurant_request=(
            result.get("restaurant_request") or {}
        ),

        available_flights=available_flights,
        available_hotels=available_hotels,
        available_restaurants=available_restaurants,

        booking_preview_id=(
            result.get("booking_preview_id") or None
        ),
    )


# ============================================================
# FRONTEND
# ============================================================

@app.get("/", include_in_schema=False)
def frontend():

    index_file = (
        Path(__file__).resolve().parents[1]
        / "web"
        / "index.html"
    )

    return FileResponse(index_file)
