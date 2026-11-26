
from agent.utils.locations import normalize_city


KNOWN_CITIES = {
    "riyadh", "jeddah", "abha", "dammam",
    "makkah", "madinah", "dubai", "khobar",
}


def apply_flight_followup(
    message: str,
    extracted: dict,
    previous_request: dict | None,
    missing_fields: list | None,
) -> dict:
    result = dict(extracted)
    previous = previous_request or {}
    missing = set(missing_fields or [])

    cleaned = message.strip().lower()

    # Only interpret a single recognized city as
    # an answer to a missing location field.
    if cleaned not in KNOWN_CITIES:
        return result

    city = normalize_city(cleaned)

    if "origin" in missing and not previous.get("origin"):
        result["origin"] = city
        result["destination"] = None

    elif (
        "destination" in missing
        and not previous.get("destination")
    ):
        result["destination"] = city
        result["origin"] = None

    return result
