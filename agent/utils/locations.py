
CITY_NAMES = {
    "الرياض": "Riyadh",
    "رياض": "Riyadh",
    "riyadh": "Riyadh",
    "جدة": "Jeddah",
    "جده": "Jeddah",
    "jeddah": "Jeddah",
    "مكة": "Makkah",
    "مكه": "Makkah",
    "makkah": "Makkah",
    "الدمام": "Dammam",
    "دمام": "Dammam",
    "dammam": "Dammam",
    "دبي": "Dubai",
    "dubai": "Dubai",
    "المدينة المنورة": "Madinah",
    "المدينة": "Madinah",
    "madinah": "Madinah",
}


def normalize_city(value):
    if not isinstance(value, str):
        return value

    cleaned = value.strip()

    return CITY_NAMES.get(
        cleaned.lower(),
        cleaned,
    )


def normalize_location_fields(data: dict) -> dict:
    result = dict(data)

    for field in ("origin", "destination", "city"):
        if field in result:
            result[field] = normalize_city(result[field])

    return result
