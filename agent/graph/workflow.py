
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver

from agent.graph.state import NashmiState
from agent.nodes.session import start_session
from agent.nodes.intent import classify_intent
from agent.nodes.hotel_extraction import extract_hotel_node

from tools.hotel_tools import search_hotels
from tools.schemas.hotel import HotelSearchRequest

from agent.nodes.follow_up import ask_hotel_follow_up

from tools.restaurant_tools import search_restaurants
from tools.schemas.common import RestaurantSearchRequest
from pydantic import ValidationError

from agent.nodes.restaurant_extraction import (
    extract_restaurant_node,
    ask_restaurant_follow_up,
)

from agent.nodes.hotel_availability import check_hotel_availability_node
from agent.nodes.restaurant_availability import (
    check_restaurant_options_node,
)
from agent.nodes.flight_extraction import (
    extract_flight_node,
    ask_flight_follow_up,
)
from tools.flight_tools import search_flights
from tools.schemas.flight import FlightSearchRequest

from agent.nodes.flight_availability import check_flight_options_node
from agent.nodes.flight_booking import select_flight_and_preview
from agent.nodes.booking_confirmation import confirm_booking_node
from agent.nodes.service_booking import select_service_and_preview
from agent.nodes.search_switch import switch_search_node


def hotel_node(state: NashmiState):
    hotel_data = state.get("hotel_request")

    if hotel_data is None:
        return {
            "status": "missing_hotel_parameters",
            "hotel_results": [],
        }

    try:
        request = HotelSearchRequest.model_validate(hotel_data)
    except ValueError:
        return {
            "status": "invalid_hotel_parameters",
            "hotel_results": [],
        }

    hotels = search_hotels(request)

    return {
        "status": "hotel_search_completed",
        "hotel_results": [
            hotel.model_dump() for hotel in hotels
        ],
    }


def restaurant_node(state: NashmiState):
    data = state.get("restaurant_request")

    if not data:
        return {
            "status": "missing_restaurant_parameters",
            "search_results": [],
        }

    try:
        request = RestaurantSearchRequest.model_validate(data)
    except ValidationError:
        return {
            "status": "invalid_restaurant_parameters",
            "search_results": [],
        }

    restaurants = search_restaurants(request)

    return {
        "status": "restaurant_search_completed",
        "search_results": [
            restaurant.model_dump()
            for restaurant in restaurants
        ],
    }


def route_after_restaurant_extraction(state: NashmiState):
    if state.get("status") == "invalid_restaurant_parameters":
        return "invalid"

    if state.get("missing_fields"):
        return "missing"

    return "complete"


def flight_node(state: NashmiState):
    data = state.get("flight_request")

    if not data:
        return {
            "status": "missing_flight_parameters",
            "flight_results": [],
        }

    try:
        request = FlightSearchRequest.model_validate(data)
    except ValidationError as exc:
        return {
            "status": "invalid_flight_parameters",
            "flight_results": [],
            "validation_errors": exc.errors(),
        }

    flights = search_flights(request)

    return {
        "status": "flight_search_completed",
        "flight_results": [
            flight.model_dump()
            for flight in flights
        ],
    }


def route_after_flight_extraction(state: NashmiState):
    if state.get("status") == "invalid_flight_parameters":
        return "invalid"

    if state.get("missing_fields"):
        return "missing"

    return "complete"

def unknown_node(state: NashmiState):
    return {"status": "unsupported_request"}


def route_intent(state: NashmiState):
    return state.get("intent", "unknown")


def route_after_extraction(state: NashmiState):
    if state.get("status") == "invalid_hotel_parameters":
        return "invalid"

    if state.get("missing_fields"):
        return "missing"

    return "complete"


checkpointer = InMemorySaver()


def route_after_search_switch(state: NashmiState) -> str:
    # Never continue searching if cancellation failed.
    if state.get("status") != "search_switch_ready":
        return "failed"

    target = state.get("requested_search_intent")

    if target in {
        "flight_search",
        "hotel_search",
        "restaurant_search",
    }:
        return target

    return "failed"


def build_graph():
    graph = StateGraph(NashmiState)

    # Register nodes
    graph.add_node("start_session", start_session)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("extract_hotel", extract_hotel_node)
    graph.add_node("hotel", hotel_node)
    graph.add_node("restaurant", restaurant_node)
    graph.add_node("extract_restaurant", extract_restaurant_node)
    graph.add_node("ask_restaurant_follow_up", ask_restaurant_follow_up)
    graph.add_node("flight", flight_node)
    graph.add_node("unknown", unknown_node)
    graph.add_node("extract_flight", extract_flight_node)
    graph.add_node("ask_flight_follow_up", ask_flight_follow_up)
    graph.add_node("ask_hotel_follow_up", ask_hotel_follow_up)
    graph.add_node(
        "hotel_availability",
        check_hotel_availability_node,
    )

    graph.add_node(
        "restaurant_availability",
        check_restaurant_options_node,
    )
    graph.add_node("flight_availability", check_flight_options_node)
    graph.add_node("flight_selection", select_flight_and_preview)

    graph.add_node("booking_confirmation", confirm_booking_node)
    graph.add_node("service_selection", select_service_and_preview)
    graph.add_node("search_switch", switch_search_node)

    # Start workflow
    graph.add_edge(START, "start_session")
    graph.add_edge("start_session", "classify_intent")

    # Route based on detected intent

    graph.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "hotel_search": "extract_hotel",
            "restaurant_search": "extract_restaurant",
            "flight_search": "extract_flight",
            "flight_selection": "flight_selection",
            "service_selection": "service_selection",
            "booking_confirmation": "booking_confirmation",
            "search_switch": "search_switch",
            "unknown": "unknown",
        },
    )

    # Route based on extracted hotel parameters
    graph.add_conditional_edges(
        "extract_hotel",
        route_after_extraction,
        {
            "complete": "hotel",
            "missing": "ask_hotel_follow_up",
            "invalid": END,
        },
    )

    graph.add_conditional_edges(
        "extract_restaurant",
        route_after_restaurant_extraction,
        {
            "complete": "restaurant",
            "missing": "ask_restaurant_follow_up",
            "invalid": END,
        },
    )

    graph.add_conditional_edges(
        "extract_flight",
        route_after_flight_extraction,
        {
            "complete": "flight",
            "missing": "ask_flight_follow_up",
            "invalid": END,
        },
    )


    graph.add_conditional_edges(
        "search_switch",
        route_after_search_switch,
        {
            "hotel_search": "extract_hotel",
            "restaurant_search": "extract_restaurant",
            "flight_search": "extract_flight",
            "failed": END,
        },
    )



    graph.add_edge("ask_flight_follow_up", END)

    graph.add_edge("ask_restaurant_follow_up", END)

    graph.add_edge("ask_hotel_follow_up", END)

    graph.add_edge("hotel", "hotel_availability")
    graph.add_edge("hotel_availability", END)

    graph.add_edge("restaurant", "restaurant_availability")
    graph.add_edge("restaurant_availability", END)

    graph.add_edge("flight", "flight_availability")
    graph.add_edge("flight_availability", END)
    graph.add_edge("flight_selection", END)

    graph.add_edge("booking_confirmation", END)
    graph.add_edge("service_selection", END)

    graph.add_edge("unknown", END)

    return graph.compile(checkpointer=InMemorySaver())
