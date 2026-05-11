from typing import Any

from sqlmodel import Session

from app.services.pricing import compute_dynamic_price
from app.services.seats import auto_select_seats, get_seat_map


PLAN_TYPES = ["CONSERVATIVE", "BALANCED", "ADVENTUROUS"]


def _build_plan(
    session: Session,
    candidate: dict[str, Any],
    plan_type: str,
    party_size: int,
    experience_mode: str,
) -> dict[str, Any]:
    seat_map = get_seat_map(session, candidate["id"])
    seats = auto_select_seats(seat_map, party_size)
    pricing = compute_dynamic_price(session, candidate["id"], candidate["base_price"])
    total = round(pricing["price"] * party_size, 2)

    rationale = [
        f"{candidate['movie_title']} is rated {candidate['movie_rating']}.",
        f"{candidate['format']} show at {candidate['theatre_name']} starts at {candidate['start_time']}.",
        f"Estimated total for {party_size} seats is Rs {round(total)}.",
    ]

    if plan_type == "CONSERVATIVE":
        rationale.append("This option minimizes price and timing risk.")
    elif plan_type == "BALANCED":
        rationale.append("This option balances rating, convenience, and value.")
    else:
        rationale.append("This option leans into premium format and standout experience.")

    if experience_mode == "date_night":
        rationale.append("The timing and format make it a stronger date-night experience.")

    return {
        "title": f"{plan_type.title()} pick: {candidate['movie_title']}",
        "summary": (
            f"{candidate['movie_title']} at {candidate['theatre_name']} in {candidate['city']} "
            f"({candidate['format']}) for roughly Rs {round(total)} total."
        ),
        "plan_type": plan_type,
        "confidence": min(0.99, 0.58 + candidate.get("discovery_score", 0) / 10),
        "showtime_id": candidate["id"],
        "theatre_id": candidate["theatre_id"],
        "seats": seats,
        "estimated_total": total,
        "rationale": rationale,
        "metadata": {
            "pricing": pricing,
            "candidate": candidate,
        },
    }


def generate_plans(session: Session, intent: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not candidates:
        return []

    party_size = max(intent.get("party_size") or 2, 1)
    experience_mode = intent.get("experience_mode") or "balanced"

    budget_sorted = sorted(candidates, key=lambda item: item["base_price"])
    balanced_sorted = sorted(
        candidates,
        key=lambda item: (-item.get("discovery_score", 0), item["base_price"]),
    )
    adventurous_sorted = sorted(
        candidates,
        key=lambda item: (
            item["format"] != "IMAX",
            -(item.get("movie_rating") or 0),
            -item["base_price"],
        ),
    )

    sources = [budget_sorted[0], balanced_sorted[0], adventurous_sorted[0]]
    plans: list[dict[str, Any]] = []
    seen_showtimes: set[int] = set()

    for plan_type, candidate in zip(PLAN_TYPES, sources):
        if candidate["id"] in seen_showtimes:
            fallback = next((item for item in balanced_sorted if item["id"] not in seen_showtimes), candidate)
            candidate = fallback
        seen_showtimes.add(candidate["id"])
        plans.append(_build_plan(session, candidate, plan_type, party_size, experience_mode))

    return plans
