from typing import TypedDict


class BookingGraphState(TypedDict, total=False):
    message: str
    intent: dict
    candidates: list[dict]
    seat_recommendations: dict
    selected_plan: dict
    booking_result: dict
    notifications: list[dict]


def build_langgraph_blueprint() -> dict:
    return {
        "nodes": [
            "planner_agent",
            "search_agent",
            "seat_optimization_agent",
            "pricing_agent",
            "booking_agent",
            "notification_agent",
            "recommendation_agent",
        ],
        "edges": [
            ["planner_agent", "search_agent"],
            ["search_agent", "seat_optimization_agent"],
            ["seat_optimization_agent", "pricing_agent"],
            ["pricing_agent", "booking_agent"],
            ["booking_agent", "notification_agent"],
            ["booking_agent", "recommendation_agent"],
        ],
        "checkpointing": "PostgreSQL workflow events and agent sessions",
        "memory": "UserPreferenceMemory plus booking history features",
    }

