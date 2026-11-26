
from unittest.mock import patch

from agent.graph.workflow import build_graph


def test_flight_search_graph():
    extracted_data = {
        "origin": "Riyadh",
        "destination": "Dubai",
        "departure_date": "2026-12-20",
        "passengers": 2,
        "cabin": "economy",
        "direct_only": True,
    }

    with patch(
        "agent.nodes.flight_extraction.extract_flight_parameters",
        return_value=extracted_data,
    ):
        graph = build_graph()

        result = graph.invoke(
            {
                "user_message": (
                    "Find a direct economy flight from Riyadh "
                    "to Dubai on December 20 for two passengers"
                ),
            },
            config={
                "configurable": {
                    "thread_id": "flight-integration-test"
                }
            },
        )

    assert result["intent"] == "flight_search"
    assert result["status"] == "flight_availability_checked"
    assert result["missing_fields"] == []
    assert len(result["available_flights"]) == 2
    assert all(
        flight["available_seats"] >= 2
        for flight in result["available_flights"]
    )

    assert len(result["flight_results"]) == 2

    for flight in result["flight_results"]:
        assert flight["origin"] == "Riyadh"
        assert flight["destination"] == "Dubai"
        assert flight["departure_date"] == "2026-12-20"
        assert flight["cabin"] == "economy"
        assert flight["direct"] is True
