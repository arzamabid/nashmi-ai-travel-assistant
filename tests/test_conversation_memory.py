
from agent.graph.workflow import build_graph


def test_graph_remembers_state():
    graph = build_graph()

    config = {
        "configurable": {
            "thread_id": "memory-test-001"
        }
    }

    graph.invoke(
        {
            "user_message": "Find a hotel in Jeddah"
        },
        config=config,
    )

    saved_state = graph.get_state(config).values

    assert saved_state["user_message"] == "Find a hotel in Jeddah"
    assert saved_state["intent"] == "hotel_search"
