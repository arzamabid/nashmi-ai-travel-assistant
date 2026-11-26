
import re
from datetime import date, datetime


MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def normalize_flight_parameters(
    message: str,
    extracted: dict,
    today: date | None = None,
) -> dict:
    result = dict(extracted)
    today = today or date.today()

    # Match "20 Dec" or "20 December".
    pattern = (
        r"\b(\d{1,2})\s+"
        r"(" + "|".join(MONTHS.keys()) + r")"
        r"(?:\s+(\d{4}))?\b"
    )

    match = re.search(
        pattern,
        message.lower(),
    )

    if match:
        day = int(match.group(1))
        month = MONTHS[match.group(2)]
        explicit_year = match.group(3)

        year = (
            int(explicit_year)
            if explicit_year
            else today.year
        )

        try:
            departure = date(year, month, day)

            # Infer next occurrence only if the
            # user did not supply a year.
            if not explicit_year and departure < today:
                departure = date(year + 1, month, day)

            result["departure_date"] = departure.isoformat()

        except ValueError:
            # Let existing schema validation handle
            # genuinely invalid dates.
            pass

    # Recognize explicit passenger counts.
    passenger_match = re.search(
        r"\b(\d+)\s*(?:passengers?|guests?|people|persons?)\b",
        message.lower(),
    )

    if passenger_match:
        result["passengers"] = int(passenger_match.group(1))

    return result
