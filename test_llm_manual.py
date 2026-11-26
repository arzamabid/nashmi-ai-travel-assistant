
from agent.llm.hotel_extractor import extract_hotel_parameters

result = extract_hotel_parameters(
    "Find a five-star hotel in Jeddah for two guests "
    "from December 10 to December 12, 2026, "
    "under 800 SAR per night."
)

print(result)
