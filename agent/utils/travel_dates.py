
import re
from datetime import date


def normalize_hotel_dates(
    message: str,
    extracted: dict,
    today: date | None = None,
) -> dict:
    result = dict(extracted)

    today = today or date.today()

    # Do not change dates if the user explicitly
    # supplied a four-digit year.
    if re.search(r"\b(?:19|20)\d{2}\b", message):
        return result

    check_in_value = result.get("check_in_date")
    check_out_value = result.get("check_out_date")

    if not check_in_value or not check_out_value:
        return result

    try:
        check_in = date.fromisoformat(check_in_value)
        check_out = date.fromisoformat(check_out_value)
    except (TypeError, ValueError):
        return result

    # Find the next occurrence of the check-in date.
    year = today.year

    while True:
        try:
            check_in = check_in.replace(year=year)
        except ValueError:
            year += 1
            continue

        if check_in >= today:
            break

        year += 1

    # Checkout might fall in the next calendar year.
    checkout_year = check_in.year

    while True:
        try:
            check_out = check_out.replace(
                year=checkout_year
            )
        except ValueError:
            checkout_year += 1
            continue

        if check_out > check_in:
            break

        checkout_year += 1

    result["check_in_date"] = check_in.isoformat()
    result["check_out_date"] = check_out.isoformat()

    return result
