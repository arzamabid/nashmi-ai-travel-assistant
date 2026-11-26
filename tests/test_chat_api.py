
from fastapi.testclient import TestClient

import apps.api.main as api_module


def test_chat_endpoint(monkeypatch):
    calls = []

    class FakeGraph:
        def invoke(self, state, config):
            calls.append({
                "state": state,
                "config": config,
            })

            return {
                "intent": "flight_search",
                "status": "flight_availability_checked",
                "available_flights": [
                    {
                        "flight_id": "FLT-001",
                        "price_sar": 250,
                    }
                ],
            }

    monkeypatch.setattr(
        api_module,
        "nashmi_graph",
        FakeGraph(),
    )

    client = TestClient(api_module.app)

    response = client.post(
        "/chat",
        json={
            "user_id": "USER-001",
            "session_id": "trip-001",
            "message": "Find flights to Jeddah",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == "trip-001"
    assert data["intent"] == "flight_search"
    assert data["status"] == "flight_availability_checked"
    assert len(data["available_flights"]) == 1
    assert data["available_flights"][0]["flight_id"] == "FLT-001"

    assert calls[0]["state"]["user_message"] == (
        "Find flights to Jeddah"
    )

    assert calls[0]["config"]["configurable"]["thread_id"] == (
        "USER-001:trip-001"
    )


def test_same_session_reuses_thread(monkeypatch):
    thread_ids = []

    class FakeGraph:
        def invoke(self, state, config):
            thread_ids.append(
                config["configurable"]["thread_id"]
            )

            return {
                "intent": "flight_selection",
                "status": "awaiting_booking_confirmation",
                "response": "Would you like to confirm?",
                "booking_preview_id": "PREVIEW-TEST-001",
            }

    monkeypatch.setattr(
        api_module,
        "nashmi_graph",
        FakeGraph(),
    )

    client = TestClient(api_module.app)

    for message in [
        "Find a flight",
        "The second one",
    ]:
        response = client.post(
            "/chat",
            json={
                "user_id": "USER-001",
                "session_id": "trip-001",
                "message": message,
            },
        )

        assert response.status_code == 200

    assert thread_ids == [
        "USER-001:trip-001",
        "USER-001:trip-001",
    ]


def test_chat_rejects_empty_message():
    client = TestClient(api_module.app)

    response = client.post(
        "/chat",
        json={
            "user_id": "USER-001",
            "session_id": "trip-001",
            "message": "",
        },
    )

    assert response.status_code == 422
