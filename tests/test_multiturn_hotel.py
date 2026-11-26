
from unittest.mock import patch
from uuid import uuid4

from agent.graph.workflow import build_graph


def test_hotel_search_across_two_messages():
    graph = build_graph()

    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    first_extraction = {
        "destination": "Jeddah",
        "stars": 5,
        "check_in_date": None,
        "check_out_date": None,
        "guests": None,
        "rooms": None,
        "max_budget_sar": None,
    }

    second_extraction = {
        "destination": None,
        "stars": None,
        "check_in_date": "2026-12-10",
        "check_out_date": "2026-12-12",
        "guests": 2,
        "rooms": 1,
        "max_budget_sar": None,
    }

    with (
        patch(
            "agent.nodes.hotel_extraction.extract_hotel_parameters",
            side_effect=[first_extraction, second_extraction],
        ) as extractor,
        patch(
            "agent.graph.workflow.search_hotels",
            return_value=[],
        ) as hotel_search,
    ):
        first = graph.invoke(
            {"user_message": "Find a five-star hotel in Jeddah"},
            config=config,
        )

        assert first["status"] == "awaiting_hotel_details"
        assert first["hotel_request"]["destination"] == "Jeddah"
        assert first["hotel_request"]["stars"] == 5

        second = graph.invoke(
            {
                "user_message":
                    "December 10 to 12, two guests, one room"
            },
            config=config,
        )

        assert second["status"] == "hotel_search_completed"
        assert second["hotel_request"]["destination"] == "Jeddah"
        assert second["hotel_request"]["stars"] == 5
        assert second["hotel_request"]["guests"] == 2
        assert second["hotel_request"]["rooms"] == 1

        assert extractor.call_count == 2
        hotel_search.assert_called_once()


def test_hotel_user_can_correct_destination():
    graph = build_graph()

    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    first_extraction = {
        "destination": "Jeddah",
        "stars": 5,
        "check_in_date": None,
        "check_out_date": None,
        "guests": None,
        "rooms": None,
        "max_budget_sar": None,
    }

    corrected_extraction = {
        "destination": "Riyadh",
        "stars": None,
        "check_in_date": "2026-12-10",
        "check_out_date": "2026-12-12",
        "guests": 2,
        "rooms": 1,
        "max_budget_sar": None,
    }

    with (
        patch(
            "agent.nodes.hotel_extraction.extract_hotel_parameters",
            side_effect=[first_extraction, corrected_extraction],
        ),
        patch(
            "agent.graph.workflow.search_hotels",
            return_value=[],
        ) as hotel_search,
    ):
        graph.invoke(
            {"user_message": "Find a five-star hotel in Jeddah"},
            config=config,
        )

        result = graph.invoke(
            {
                "user_message":
                    "Actually, make it Riyadh. "
                    "December 10 to 12, two guests, one room."
            },
            config=config,
        )

        assert result["status"] == "hotel_search_completed"
        assert result["hotel_request"]["destination"] == "Riyadh"
        assert result["hotel_request"]["stars"] == 5
        assert result["hotel_request"]["guests"] == 2

        hotel_search.assert_called_once()


def test_separate_conversations_do_not_share_memory():
    graph = build_graph()

    config_a = {
        "configurable": {"thread_id": str(uuid4())}
    }
    config_b = {
        "configurable": {"thread_id": str(uuid4())}
    }

    with patch(
        "agent.nodes.hotel_extraction.extract_hotel_parameters",
        side_effect=[
            {
                "destination": "Jeddah",
                "stars": 5,
                "check_in_date": None,
                "check_out_date": None,
                "guests": None,
                "rooms": None,
            },
            {
                "destination": "Riyadh",
                "stars": 3,
                "check_in_date": None,
                "check_out_date": None,
                "guests": None,
                "rooms": None,
            },
        ],
    ):
        graph.invoke(
            {"user_message": "Find a five-star hotel in Jeddah"},
            config=config_a,
        )

        graph.invoke(
            {"user_message": "Find a three-star hotel in Riyadh"},
            config=config_b,
        )

    state_a = graph.get_state(config_a).values
    state_b = graph.get_state(config_b).values

    assert state_a["hotel_request"]["destination"] == "Jeddah"
    assert state_a["hotel_request"]["stars"] == 5

    assert state_b["hotel_request"]["destination"] == "Riyadh"
    assert state_b["hotel_request"]["stars"] == 3

    assert state_a["hotel_request"] != state_b["hotel_request"]


def test_user_can_switch_from_hotel_to_flight():
    graph = build_graph()

    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    first_extraction = {
        "destination": "Jeddah",
        "stars": 5,
        "check_in_date": None,
        "check_out_date": None,
        "guests": None,
        "rooms": None,
        "max_budget_sar": None,
    }

    with patch(
        "agent.nodes.hotel_extraction.extract_hotel_parameters",
        return_value=first_extraction,
    ) as extractor:
        first = graph.invoke(
            {"user_message": "Find a five-star hotel in Jeddah"},
            config=config,
        )

        assert first["status"] == "awaiting_hotel_details"

        second = graph.invoke(
            {"user_message": "Actually, find a flight to Dubai"},
            config=config,
        )

        assert second["intent"] == "flight_search"
        assert second["status"] == "awaiting_flight_details"
        assert extractor.call_count == 1
