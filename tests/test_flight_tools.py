from tools.flight_tools import search_flights
from tools.schemas.flight import FlightSearchRequest


def test_flight_search_returns_matching_results():
    request = FlightSearchRequest(
        origin="Riyadh",
        destination="Dubai",
        departure_date="2026-12-20",
        passengers=2,
        cabin="economy",
        direct_only=True,
    )

    results = search_flights(request)

    assert len(results) == 2
    assert all(result.origin == "Riyadh" for result in results)
    assert all(result.destination == "Dubai" for result in results)
    assert all(result.cabin == "economy" for result in results)
    assert all(result.direct is True for result in results)


def test_flight_search_orders_by_price():
    request = FlightSearchRequest(
        origin="Riyadh",
        destination="Dubai",
        departure_date="2026-12-20",
        passengers=2,
        cabin="economy",
        direct_only=True,
    )

    results = search_flights(request)

    prices = [result.price_sar for result in results]

    assert prices == sorted(prices)


def test_flight_search_returns_empty_for_unknown_route():
    request = FlightSearchRequest(
        origin="Riyadh",
        destination="Paris",
        departure_date="2026-12-20",
        passengers=2,
        cabin="economy",
        direct_only=True,
    )

    results = search_flights(request)

    assert results == []
