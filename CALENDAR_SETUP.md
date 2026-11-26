# NASHMI — Hotel and Restaurant Availability Pickers

## Files

- `nashmi_index_all_calendars.html` → replace `apps/web/index.html` (keep a backup of yours)
- `nashmi_availability_calendar.py` → `apps/api/availability_calendar.py`

## API integration (small edits to existing apps/api/main.py)

Add at the top:

```python
from apps.api.availability_calendar import router as availability_calendar_router
```

Add immediately after your existing `app = FastAPI(...)` block:

```python
app.include_router(availability_calendar_router)
```

Add to `class ChatResponse(BaseModel):`:

```python
hotel_request: dict = Field(default_factory=dict)
restaurant_request: dict = Field(default_factory=dict)
```

Add to the existing `return ChatResponse(...)` within `/chat`:

```python
hotel_request=result.get("hotel_request") or {},
restaurant_request=result.get("restaurant_request") or {},
```

Retain the pre-existing `flight_request` response field required by the flight calendar. If that field is not yet present, add it in the same way. Keep all existing routes, booking functions, and response logic unchanged.

## Run / test

```bash
python -m py_compile apps/api/main.py apps/api/availability_calendar.py
python -m pytest tests/ -q
python -m uvicorn apps.api.main:app --reload --port 8000
```

Manual API checks (while server running):

- `http://127.0.0.1:8000/hotels/calendar?city=Riyadh&year=2026&month=12&rooms=2`
- `http://127.0.0.1:8000/hotels/stay-check?city=Riyadh&check_in=2026-12-15&check_out=2026-12-18&rooms=2`
- `http://127.0.0.1:8000/restaurants/calendar?city=Riyadh&year=2026&month=12&party_size=4`

**Browser tests:**

1. "Find a hotel in Riyadh" → click **View available hotel dates**, choose guests/rooms, select green check-in and a later checkout, then **Check this hotel stay**. The server verifies one hotel can cover **every night** before the chat search is submitted. Date ranges without full inventory show a helpful error.
2. "Find restaurants in Riyadh" → click **View restaurant dates & times**, choose party size, select a green date and then an available time slot. The chat receives a fully specified query.
3. Repeat the existing flight flow to ensure it still works.
4. Toggle Arabic and verify RTL labels/calendar functionality.

## Safety / scope

The endpoints read local demo inventory only; they do not reserve seats, rooms, or tables. Green hotel days mean one or more hotels have rooms *for that night*, not necessarily for the entire requested stay; the separate stay-check endpoint verifies the complete stay. Restaurant time slots represent an exact party size and available status. Prices and slots can change before the final booking confirmation.

The selected hotel/restaurant date or time is currently sent as a **complete chat request** through the existing LLM extractor (the same MVP approach used by the flight calendar). A future structured action can bypass the LLM entirely. This bundle was syntax-checked locally but cannot be integration-tested against your Mac's database from here.
