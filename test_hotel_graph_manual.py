
from agent.graph.workflow import build_graph

graph = build_graph()


result = graph.invoke({
    "user_message": (
        "Find a five-star hotel in Jeddah "
        "for two guests and one room, "
        "December 10 to 12, 2026, "
        "under 800 SAR per night."
    )
})

print("Intent:", result.get("intent"))
print("Status:", result.get("status"))
print("Hotels:", result.get("hotel_results"))
print("Missing fields:", result.get("missing_fields"))


for hotel in result["hotel_results"]:
    print(
        hotel["name"],
        "-",
        hotel["price_per_night_sar"],
        "SAR/night",
    )
