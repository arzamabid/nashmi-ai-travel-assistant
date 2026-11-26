
from unittest.mock import MagicMock, patch

from tools.flight_availability_tools import check_flight_availability
from tools.schemas.flight_availability import FlightAvailabilityRequest


def run_check(flight, inventory, passengers=2):
    session = MagicMock()

    session.query.return_value.filter.return_value.first.side_effect = [
        flight,
        inventory,
    ] if flight is not None else [None]

    context = MagicMock()
    context.__enter__.return_value = session

    with patch(
        "tools.flight_availability_tools.SessionLocal",
        return_value=context,
    ):
        return check_flight_availability(
            FlightAvailabilityRequest(
                flight_id="FLT-005",
                passengers=passengers,
            )
        )


def test_flight_has_enough_seats():
    flight = MagicMock(id=5)
    inventory = MagicMock(available_seats=20)

    result = run_check(flight, inventory, passengers=2)

    assert result.available is True
    assert result.available_seats == 20


def test_flight_has_insufficient_seats():
    flight = MagicMock(id=5)
    inventory = MagicMock(available_seats=1)

    result = run_check(flight, inventory, passengers=2)

    assert result.available is False
    assert result.available_seats == 1


def test_flight_does_not_exist():
    result = run_check(None, None)

    assert result.available is False
    assert result.available_seats == 0


def test_flight_has_no_inventory():
    flight = MagicMock(id=5)

    result = run_check(flight, None)

    assert result.available is False
    assert result.available_seats == 0
