
import json

from unittest.mock import MagicMock, patch

from agent.llm.restaurant_extractor import (
    extract_restaurant_parameters,
)


def test_restaurant_extractor():
    extracted = {
        "city": "Riyadh",
        "cuisine": "Italian",
        "price_level": None,
        "family_friendly": None,
        "date": "2026-11-23",
        "time": "20:00",
        "party_size": 4,
    }

    fake_response = MagicMock()
    fake_response.message.content = json.dumps(extracted)

    with patch(
        "agent.llm.restaurant_extractor.chat",
        return_value=fake_response,
    ):
        result = extract_restaurant_parameters(
            "Find an Italian restaurant in Riyadh "
            "tomorrow at 8 PM for four people."
        )

    assert result["city"] == "Riyadh"
    assert result["cuisine"] == "Italian"
    assert result["time"] == "20:00"
    assert result["party_size"] == 4
