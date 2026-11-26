
import pytest
from pydantic import ValidationError

from tools.schemas.restaurant import RestaurantSearchRequest


def test_valid_restaurant_request():
    request = RestaurantSearchRequest(
        city="Riyadh",
        cuisine="Italian",
        party_size=4,
        max_budget_sar=200,
    )

    assert request.city == "Riyadh"
    assert request.party_size == 4
    assert request.max_budget_sar == 200


def test_invalid_party_size():
    with pytest.raises(ValidationError):
        RestaurantSearchRequest(
            city="Riyadh",
            party_size=-4,
        )


def test_invalid_budget():
    with pytest.raises(ValidationError):
        RestaurantSearchRequest(
            city="Riyadh",
            party_size=4,
            max_budget_sar=-100,
        )


def test_optional_filters():
    request = RestaurantSearchRequest(
        city="Jeddah",
        party_size=2,
    )

    assert request.cuisine is None
    assert request.date is None
    assert request.time is None
    assert request.family_friendly is None
