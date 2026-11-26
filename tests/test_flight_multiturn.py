
from unittest.mock import patch

from agent.graph.workflow import build_graph


def test_flight_multiturn():
    first_extraction = {
        "origin": "Riyadh",
        "destination": "Dubai",
        "departure_date": None,
        "passengers": None,
        "cabin": None,
        "direct_only": None,
    }

    second_extraction = {
        "origin": None,
        "destination": None,
        "departure_date": "2026-12-20",
        "passengers": 2,
        "cabin": None,
        "direct_only": None,
    }

    with patch(
        "agent.nodes.flight_extraction.extract_flight_parameters",
        side_effect=[first_extraction, second_extraction],
    ):
        graph = build_graph()

        config = {
            "configurable": {
                "thread_id": "flight-multiturn-test"
            }
        }

        first = graph.invoke(
            {
                "user_message": "Find a flight from Riyadh to Dubai"
            },
            config=config,
        )

        assert first["status"] == "awaiting_flight_details"
        assert set(first["missing_fields"]) == {
            "departure_date",
            "passengers",
        }

        second = graph.invoke(
            {
                "user_message": "December 20, for two passengers"
            },
            config=config,
        )

    assert second["status"] == "flight_availability_checked"
    assert second["flight_request"]["origin"] == "Riyadh"
    assert second["flight_request"]["destination"] == "Dubai"
    assert second["flight_request"]["departure_date"] == "2026-12-20"
    assert second["flight_request"]["passengers"] == 2

    assert isinstance(second["flight_results"], list)
