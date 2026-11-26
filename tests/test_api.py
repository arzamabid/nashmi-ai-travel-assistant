from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_hotel_search_validation():
    response = client.post(
        "/hotels/search",
        json={}
    )

    assert response.status_code == 422



def test_hotel_search_returns_results():
    response = client.post(
        "/hotels/search",
        json={
            "destination": "Jeddah",
            "check_in_date": "2026-12-10",
            "check_out_date": "2026-12-12",
            "guests": 2,
            "rooms": 1,
            "stars": 5
        }
    )

    assert response.status_code == 200

    hotels = response.json()

    assert len(hotels) > 0
    assert all(hotel["city"] == "Jeddah" for hotel in hotels)
    assert all(hotel["stars"] == 5 for hotel in hotels)
