from __future__ import annotations

import math
from typing import Any

from sqlmodel import Session

from app.services.seats import get_seat_map


def _seat_score(
    row_index: int,
    col_index: int,
    row_count: int,
    col_count: int,
    price: float,
    preferences: dict[str, Any],
) -> float:
    ideal_row = row_count * float(preferences.get("ideal_row_ratio", 0.62))
    ideal_col = (col_count - 1) / 2
    row_distance = abs(row_index - ideal_row) / max(row_count, 1)
    center_distance = abs(col_index - ideal_col) / max(col_count, 1)
    price_ceiling = float(preferences.get("price_ceiling") or max(price, 1))
    price_penalty = max(price - price_ceiling, 0) / max(price_ceiling, 1)
    popularity_bonus = 0.06 if 0.35 <= row_index / max(row_count, 1) <= 0.75 else 0
    return round(1 - (row_distance * 0.42 + center_distance * 0.38 + price_penalty * 0.20) + popularity_bonus, 4)


def _group_contiguous_blocks(row: list[dict[str, Any]], party_size: int) -> list[list[dict[str, Any]]]:
    blocks: list[list[dict[str, Any]]] = []
    for start in range(0, max(len(row) - party_size + 1, 0)):
        block = row[start : start + party_size]
        if len(block) == party_size and all(seat.get("status") in {"AVAILABLE", "HELD_BY_YOU"} for seat in block):
            blocks.append(block)
    return blocks


def rank_seat_blocks(
    session: Session,
    showtime_id: int,
    party_size: int,
    preferences: dict[str, Any] | None = None,
    session_key: str | None = None,
) -> dict[str, Any]:
    preferences = preferences or {}
    seat_map = get_seat_map(session, showtime_id, session_key=session_key)
    row_count = len(seat_map)
    recommendations: list[dict[str, Any]] = []

    for row_index, row in enumerate(seat_map):
        col_count = len(row)
        for block in _group_contiguous_blocks(row, party_size):
            first_col = next(i for i, s in enumerate(row) if s["id"] == block[0]["id"])
            prices = [float(seat.get("price") or preferences.get("base_price") or 250) for seat in block]
            avg_col = first_col + (len(block) - 1) / 2
            avg_price = sum(prices) / len(prices)
            score = _seat_score(row_index, int(avg_col), row_count, col_count, avg_price, preferences)
            viewing_angle = 1 - abs(avg_col - ((col_count - 1) / 2)) / max(col_count, 1)
            legibility = 1 - abs((row_index / max(row_count, 1)) - 0.62)
            recommendations.append(
                {
                    "seats": [seat["id"] for seat in block],
                    "row": block[0]["id"][0],
                    "total_price": round(sum(prices), 2),
                    "score": score,
                    "viewing_quality": round((viewing_angle * 0.52 + legibility * 0.48), 4),
                    "rationale": [
                        "contiguous seats for the full group",
                        "balanced screen distance and center alignment",
                        "within preferred value band" if avg_price <= float(preferences.get("price_ceiling") or math.inf) else "above preferred value band",
                    ],
                }
            )

    ranked = sorted(recommendations, key=lambda item: (-item["score"], item["total_price"]))
    cheapest = sorted(recommendations, key=lambda item: (item["total_price"], -item["score"]))
    premium = sorted(recommendations, key=lambda item: (-item["viewing_quality"], -item["score"]))
    return {
        "showtime_id": showtime_id,
        "party_size": party_size,
        "best_overall": ranked[:5],
        "best_value": cheapest[:5],
        "premium_experience": premium[:5],
        "available_blocks": len(ranked),
    }
