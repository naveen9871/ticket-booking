import json
from typing import Any
from sqlmodel import Session, select

from app.agents.llm import call_llm, extract_tool_call
from app.models import Movie, Showtime

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_movie_details",
            "description": "Update movie metadata like description, tags, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer"},
                    "description": {"type": "string"},
                    "tags": {"type": "string"},
                },
                "required": ["movie_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_base_prices",
            "description": "Adjust base prices for showtimes",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer"},
                    "adjustment_factor": {"type": "number", "description": "e.g. 1.1 for 10% increase"},
                },
                "required": ["movie_id", "adjustment_factor"],
            },
        },
    },
]

SYSTEM_PROMPT = """
You are Ticketly's Admin Operations Assistant.
You help admins manage the catalog, adjust prices, and generate marketing content.
If given a movie name but not an ID, search for it first (implied search for admin).
"""

def handle_admin_message(session: Session, message: str) -> dict[str, Any]:
    llm = call_llm(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        tools=TOOLS,
    )
    tool_call = extract_tool_call(llm) if llm else None

    if tool_call:
        name, args = tool_call
        if name == "update_movie_details":
            movie = session.get(Movie, args["movie_id"])
            if not movie: return {"type": "error", "message": "Movie not found"}
            if "description" in args: movie.description = args["description"]
            if "tags" in args: movie.tags = args["tags"]
            session.add(movie)
            session.commit()
            return {"type": "success", "message": f"Updated {movie.title}", "data": movie}
            
        if name == "adjust_base_prices":
            showtimes = session.exec(select(Showtime).where(Showtime.movie_id == args["movie_id"])).all()
            for s in showtimes:
                s.base_price = round(s.base_price * args["adjustment_factor"], 2)
                session.add(s)
            session.commit()
            return {"type": "success", "message": f"Adjusted prices for {len(showtimes)} showtimes"}

    # If no tool call, generate creative content using LLM
    content_prompt = f"Write a catchy 2-sentence marketing description for this: {message}"
    creative = call_llm([{"role": "user", "content": content_prompt}])
    
    return {
        "type": "message",
        "message": creative or "I can help you update movies or adjust prices. Just tell me what to do.",
    }
