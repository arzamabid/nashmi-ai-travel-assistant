
import pytest

from agent.graph.workflow import build_graph


@pytest.fixture
def graph():
    return build_graph()


@pytest.mark.parametrize(
    "message, expected_status, thread_id",
    [
        (
            "Find a hotel in Jeddah",
            "awaiting_hotel_details",
            "test-hotel",
        ),
        (
                "Find a restaurant in Riyadh",
                "awaiting_restaurant_details",
                "test-restaurant",
        ),
        (
            "Find a flight to Dubai",
            "awaiting_flight_details",
            "test-flight",
        ),
        (
            "Hello",
            "unsupported_request",
            "test-unknown",
        ),
    ],
)
def test_graph_routes_requests(
    graph, message, expected_status, thread_id
):
    result = graph.invoke(
        {"user_message": message},
        config={
            "configurable": {
                "thread_id": thread_id
            }
        },
    )

    assert result["status"] == expected_status
