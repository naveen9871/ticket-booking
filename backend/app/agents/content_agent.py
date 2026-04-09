from typing import Any

from app.agents.llm import call_llm


SYSTEM_PROMPT = "You are a movie marketing copywriter. Create short, catchy blurbs."


def generate_blurb(title: str, genre: str) -> dict[str, Any]:
    llm = call_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Write a 2 sentence blurb for {title} ({genre})."},
    ])
    if not llm:
        return {"blurb": f"Experience the magic of {title} — a must-watch {genre} event."}

    text = llm["choices"][0]["message"]["content"]
    return {"blurb": text}
