from typing import Any


def build_recovery_message(intent: dict[str, Any], reason: str) -> dict[str, Any]:
    city = intent.get("city")
    budget = intent.get("budget_max")
    details = []
    if city:
        details.append(city)
    if budget:
        details.append(f"budget up to Rs {budget}")
    suffix = f" for {' and '.join(details)}" if details else ""
    return {
        "type": "message",
        "message": (
            f"I could not complete the ideal booking flow{suffix} because {reason}. "
            "Try a broader city, a higher budget, or ask me for the next best available show."
        ),
    }


def normalize_failure(exc: Exception) -> str:
    text = str(exc).strip()
    if not text:
        return "the system hit an unexpected issue"
    return text[0].lower() + text[1:]
