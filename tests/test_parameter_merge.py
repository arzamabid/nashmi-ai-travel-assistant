
from agent.utils.merge import merge_parameters


def test_merge_keeps_previous_information():
    previous = {
        "destination": "Jeddah",
        "stars": 5,
    }

    new = {
        "destination": None,
        "check_in_date": "2026-12-10",
        "check_out_date": "2026-12-12",
        "guests": 2,
        "rooms": 1,
    }

    result = merge_parameters(previous, new)

    assert result["destination"] == "Jeddah"
    assert result["stars"] == 5
    assert result["guests"] == 2
    assert result["rooms"] == 1


def test_merge_allows_corrections():
    previous = {
        "destination": "Jeddah",
        "guests": 2,
    }

    new = {
        "destination": "Riyadh",
        "guests": 3,
    }

    result = merge_parameters(previous, new)

    assert result["destination"] == "Riyadh"
    assert result["guests"] == 3
