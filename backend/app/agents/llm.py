"""
True agentic LLM layer — supports Claude (Anthropic), Gemini, and OpenAI.

Set LLM_PROVIDER in .env to switch:
  - "claude"  → Anthropic claude-haiku-4-5 (default, recommended)
  - "gemini"  → Google Gemini 2.0 Flash
  - "openai"  → OpenAI GPT-4o-mini

The agentic loop:
  1. Send user message + conversation history + tools to LLM
  2. LLM decides which tool to call (or responds directly)
  3. We execute the tool, append the result, send back to LLM
  4. Repeat until LLM gives a final text response (max 8 iterations)
"""

from __future__ import annotations

import json
from typing import Any, Callable

from app.core.config import settings

# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Ticketly AI — an intelligent, conversational movie ticket booking assistant for India.

Your capabilities:
- Search for available showtimes by movie, city, date, format, genre, budget
- Show seat availability and recommend the best seats
- Set release-watch alerts for upcoming movies
- Explain WHY you recommend each option (price, format, rating, timing)

Personality:
- Warm, concise, helpful — never robotic or generic.
- Use Indian context: ₹ for prices, real city names.
- Ask ONE clarifying question if the request is truly ambiguous.
- When presenting options, give 2-3 choices max with clear reasoning.

Hard rules:
- NEVER invent showtimes, movies, prices, or seats — only use data returned by your tools.
- NEVER hold seats or initiate payment. Always tell the user to click "Open Seat Map →" to proceed.
- If search returns no results, explain why and suggest what to change (city, format, budget, time).
- Always show the actual ₹ price from tool results.
- Keep responses concise — under 150 words unless listing multiple options.

When showing options use this format:
1. One-line summary of what you found
2. 2-3 options: movie · theatre · format · time · ₹price · why it's good
3. "Click **Open Seat Map →** on any card to pick seats and proceed."
"""

# ── Tool definitions (provider-agnostic schema) ────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "search_showtimes",
        "description": (
            "Search for available movie showtimes matching the user's preferences. "
            "Call this whenever the user wants to find, book, or discover movies. "
            "Returns a list of showtimes with theatre, format, price, and timing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City to search in e.g. Bengaluru, Mumbai, Chennai."},
                "movie_title": {"type": "string", "description": "Specific movie title if mentioned."},
                "genre": {"type": "string", "description": "Genre filter e.g. Action, Drama, Comedy, Thriller."},
                "format": {"type": "string", "description": "Screen format: IMAX, DOLBY_ATMOS, 4DX, RECLINER, STANDARD."},
                "party_size": {"type": "integer", "description": "Number of seats needed."},
                "budget_max": {"type": "number", "description": "Maximum TOTAL budget in INR for all seats combined."},
                "date_hint": {"type": "string", "description": "Timing: today, tonight, tomorrow, weekend, friday, morning, afternoon, evening."},
            },
            "required": ["city"],
        },
    },
    {
        "name": "get_seat_availability",
        "description": (
            "Get available seat count and recommended seat groups for a specific showtime. "
            "Call this when the user picks a showtime and wants to know about seats."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "showtime_id": {"type": "integer", "description": "The showtime ID to check."},
                "party_size": {"type": "integer", "description": "How many seats to find together."},
            },
            "required": ["showtime_id"],
        },
    },
    {
        "name": "set_release_watch",
        "description": (
            "Set an alert to notify the user when bookings open for an upcoming movie. "
            "Use when the user says 'alert me', 'notify me', 'watch for', or 'remind me when bookings open'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "movie_title": {"type": "string", "description": "Movie to watch for."},
                "city": {"type": "string", "description": "City where the user wants to watch."},
                "party_size": {"type": "integer", "description": "Number of seats to look for."},
            },
            "required": ["movie_title", "city"],
        },
    },
]


# ── Main agentic loop ──────────────────────────────────────────────────────────

def run_agent_loop(
    message: str,
    history: list[dict[str, Any]],
    tool_executor: Callable[[str, dict], Any],
    max_iterations: int = 8,
) -> dict[str, Any]:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "claude":
        return _claude_agent_loop(message, history, tool_executor, max_iterations)
    elif provider == "gemini":
        return _gemini_agent_loop(message, history, tool_executor, max_iterations)
    elif provider == "openai":
        return _openai_agent_loop(message, history, tool_executor, max_iterations)
    else:
        return _error_result(f"Unknown LLM_PROVIDER '{provider}'. Set to: claude, gemini, or openai.")


# ── Claude (Anthropic) ─────────────────────────────────────────────────────────

def _claude_agent_loop(
    message: str,
    history: list[dict[str, Any]],
    tool_executor: Callable[[str, dict], Any],
    max_iterations: int,
) -> dict[str, Any]:
    if not settings.ANTHROPIC_API_KEY:
        return _error_result("ANTHROPIC_API_KEY is not set.")

    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Convert tools to Claude format
    claude_tools = [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["parameters"],
        }
        for t in TOOL_DEFINITIONS
    ]

    # Build messages from history + current message
    messages = _build_claude_messages(history, message)

    trace: list[dict] = []
    all_showtimes: list[dict] = []
    all_plans: list[dict] = []
    tool_calls_made: list[dict] = []

    for _ in range(max_iterations):
        try:
            response = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=claude_tools,
                messages=messages,
            )
        except Exception as e:
            return _error_result(f"Claude API error: {e}")

        # Collect text and tool use blocks
        text_parts = []
        tool_uses = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(block)

        # No tool calls → final answer
        if not tool_uses or response.stop_reason == "end_turn":
            return {
                "text": " ".join(text_parts).strip() or "I couldn't find what you're looking for. Could you give me more details?",
                "tool_calls": tool_calls_made,
                "plans": all_plans,
                "showtimes": all_showtimes,
                "trace": trace,
            }

        # Append assistant turn to messages
        messages.append({"role": "assistant", "content": response.content})

        # Execute tools and collect results
        tool_results = []
        for block in tool_uses:
            tool_name = block.name
            tool_args = dict(block.input)
            tool_calls_made.append({"tool": tool_name, "args": tool_args})
            trace.append({
                "agent": _tool_label(tool_name),
                "detail": _tool_detail(tool_name, tool_args),
            })

            try:
                result = tool_executor(tool_name, tool_args)
            except Exception as e:
                result = {"error": str(e)}

            # Stash structured data for frontend
            if tool_name == "search_showtimes" and isinstance(result, dict):
                all_showtimes.extend(result.get("showtimes", []))
                all_plans.extend(result.get("plans", []))
                trace[-1]["detail"] += f" → {result.get('count', 0)} found"
            if tool_name == "get_seat_availability" and isinstance(result, dict):
                trace[-1]["detail"] += f" → {result.get('available_count', 0)} seats available"

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
            })

        messages.append({"role": "user", "content": tool_results})

    return _error_result("Max iterations reached.", tool_calls_made, all_plans, all_showtimes, trace)


def _build_claude_messages(history: list[dict], message: str) -> list[dict]:
    """Convert stored history format to Claude messages format."""
    messages = []
    for turn in history:
        role = turn.get("role")
        parts = turn.get("parts", [])
        if isinstance(parts, list) and parts:
            content = parts[0] if isinstance(parts[0], str) else str(parts[0])
        else:
            content = str(parts)
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})
    return messages


# ── Gemini ─────────────────────────────────────────────────────────────────────

def _gemini_agent_loop(
    message: str,
    history: list[dict[str, Any]],
    tool_executor: Callable[[str, dict], Any],
    max_iterations: int,
) -> dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        return _error_result("GEMINI_API_KEY is not set.")

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
    except ImportError:
        return _error_result("google-generativeai package not installed.")

    gemini_tools = genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        k: genai.protos.Schema(
                            type={"string": genai.protos.Type.STRING, "integer": genai.protos.Type.INTEGER, "number": genai.protos.Type.NUMBER}.get(v.get("type", "string"), genai.protos.Type.STRING),
                            description=v.get("description", ""),
                        )
                        for k, v in t["parameters"]["properties"].items()
                    },
                    required=t["parameters"].get("required", []),
                ),
            )
            for t in TOOL_DEFINITIONS
        ]
    )

    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        tools=[gemini_tools],
    )

    contents = list(history)
    contents.append({"role": "user", "parts": [message]})

    trace: list[dict] = []
    all_showtimes: list[dict] = []
    all_plans: list[dict] = []
    tool_calls_made: list[dict] = []

    for _ in range(max_iterations):
        try:
            response = model.generate_content(contents)
        except Exception as e:
            return _error_result(f"Gemini API error: {e}")

        candidate = response.candidates[0] if response.candidates else None
        if not candidate:
            break

        text_parts, fn_calls = [], []
        for part in candidate.content.parts:
            if hasattr(part, "text") and part.text:
                text_parts.append(part.text)
            if hasattr(part, "function_call") and part.function_call.name:
                fn_calls.append(part.function_call)

        if not fn_calls:
            return {
                "text": " ".join(text_parts).strip() or "I couldn't find what you're looking for.",
                "tool_calls": tool_calls_made,
                "plans": all_plans,
                "showtimes": all_showtimes,
                "trace": trace,
            }

        contents.append({"role": "model", "parts": candidate.content.parts})

        tool_response_parts = []
        for fn in fn_calls:
            tool_name, tool_args = fn.name, dict(fn.args)
            tool_calls_made.append({"tool": tool_name, "args": tool_args})
            trace.append({"agent": _tool_label(tool_name), "detail": _tool_detail(tool_name, tool_args)})

            try:
                result = tool_executor(tool_name, tool_args)
            except Exception as e:
                result = {"error": str(e)}

            if tool_name == "search_showtimes" and isinstance(result, dict):
                all_showtimes.extend(result.get("showtimes", []))
                all_plans.extend(result.get("plans", []))
                trace[-1]["detail"] += f" → {result.get('count', 0)} found"

            tool_response_parts.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=tool_name,
                        response={"result": json.dumps(result, default=str)},
                    )
                )
            )
        contents.append({"role": "user", "parts": tool_response_parts})

    return _error_result("Max iterations reached.", tool_calls_made, all_plans, all_showtimes, trace)


# ── OpenAI ─────────────────────────────────────────────────────────────────────

def _openai_agent_loop(
    message: str,
    history: list[dict[str, Any]],
    tool_executor: Callable[[str, dict], Any],
    max_iterations: int,
) -> dict[str, Any]:
    if not settings.OPENAI_API_KEY:
        return _error_result("OPENAI_API_KEY is not set.")

    import httpx

    openai_tools = [
        {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}}
        for t in TOOL_DEFINITIONS
    ]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in history:
        role = turn.get("role")
        parts = turn.get("parts", [])
        content = parts[0] if isinstance(parts, list) and parts and isinstance(parts[0], str) else str(parts)
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    trace: list[dict] = []
    all_showtimes: list[dict] = []
    all_plans: list[dict] = []
    tool_calls_made: list[dict] = []

    for _ in range(max_iterations):
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"},
                    json={"model": settings.OPENAI_MODEL, "messages": messages, "tools": openai_tools, "temperature": 0.3},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            return _error_result(f"OpenAI API error: {e}")

        choice = data["choices"][0]
        msg = choice["message"]
        messages.append(msg)

        if not msg.get("tool_calls") or choice["finish_reason"] == "stop":
            return {
                "text": msg.get("content") or "I couldn't find what you're looking for.",
                "tool_calls": tool_calls_made,
                "plans": all_plans,
                "showtimes": all_showtimes,
                "trace": trace,
            }

        for tc in msg["tool_calls"]:
            tool_name = tc["function"]["name"]
            tool_args = json.loads(tc["function"]["arguments"])
            tool_calls_made.append({"tool": tool_name, "args": tool_args})
            trace.append({"agent": _tool_label(tool_name), "detail": _tool_detail(tool_name, tool_args)})

            try:
                result = tool_executor(tool_name, tool_args)
            except Exception as e:
                result = {"error": str(e)}

            if tool_name == "search_showtimes" and isinstance(result, dict):
                all_showtimes.extend(result.get("showtimes", []))
                all_plans.extend(result.get("plans", []))
                trace[-1]["detail"] += f" → {result.get('count', 0)} found"

            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps(result, default=str)})

    return _error_result("Max iterations reached.", tool_calls_made, all_plans, all_showtimes, trace)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _error_result(msg: str, tool_calls=None, plans=None, showtimes=None, trace=None) -> dict:
    return {
        "text": msg,
        "tool_calls": tool_calls or [],
        "plans": plans or [],
        "showtimes": showtimes or [],
        "trace": trace or [],
    }


def _tool_label(name: str) -> str:
    return {"search_showtimes": "Search Agent", "get_seat_availability": "Seat Agent", "set_release_watch": "Watch Agent"}.get(name, name)


def _tool_detail(name: str, args: dict) -> str:
    if name == "search_showtimes":
        parts = []
        if args.get("movie_title"):
            parts.append(args["movie_title"])
        if args.get("city"):
            parts.append(f"in {args['city']}")
        if args.get("format"):
            parts.append(args["format"])
        if args.get("party_size"):
            parts.append(f"for {args['party_size']} people")
        if args.get("budget_max"):
            parts.append(f"under ₹{args['budget_max']}")
        return "Searching " + (", ".join(parts) or "showtimes")
    if name == "get_seat_availability":
        return f"Checking seats for showtime #{args.get('showtime_id')}"
    if name == "set_release_watch":
        return f"Setting watch for {args.get('movie_title')} in {args.get('city')}"
    return str(args)


# ── Backward-compat shims (used by intent.py, admin_agent, content_agent) ─────

def call_llm(messages: list[dict], tools: list[dict] | None = None) -> dict | None:
    """Simple single-shot LLM call (non-agentic). Routes to active provider."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "claude" and settings.ANTHROPIC_API_KEY:
        return _claude_single_call(messages)
    elif provider == "gemini" and settings.GEMINI_API_KEY:
        return _gemini_single_call(messages)
    elif provider == "openai" and settings.OPENAI_API_KEY:
        return _openai_single_call(messages)

    # Try any available key as fallback
    if settings.ANTHROPIC_API_KEY:
        return _claude_single_call(messages)
    if settings.GEMINI_API_KEY:
        return _gemini_single_call(messages)
    return None


def _claude_single_call(messages: list[dict]) -> dict | None:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        system = next((m["content"] for m in messages if m["role"] == "system"), SYSTEM_PROMPT)
        user_msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
        if not user_msgs:
            return None
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=512,
            system=system,
            messages=user_msgs,
        )
        text = response.content[0].text if response.content else ""
        return {"choices": [{"message": {"role": "assistant", "content": text, "tool_calls": None}}]}
    except Exception as e:
        print(f"[call_llm/claude] Error: {e}")
        return None


def _gemini_single_call(messages: list[dict]) -> dict | None:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_parts = [m["content"] for m in messages if m["role"] != "system"]
        prompt = (f"System: {system}\n\n" if system else "") + "\n".join(user_parts)
        response = model.generate_content(prompt)
        return {"choices": [{"message": {"role": "assistant", "content": response.text, "tool_calls": None}}]}
    except Exception as e:
        print(f"[call_llm/gemini] Error: {e}")
        return None


def _openai_single_call(messages: list[dict]) -> dict | None:
    try:
        import httpx
        with httpx.Client(timeout=20) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": settings.OPENAI_MODEL, "messages": messages, "temperature": 0.3},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"[call_llm/openai] Error: {e}")
        return None


def extract_tool_call(response: dict | None) -> tuple[str, dict] | None:
    if not response:
        return None
    choices = response.get("choices", [])
    if not choices:
        return None
    msg = choices[0].get("message", {})
    tool_calls = msg.get("tool_calls") or []
    if not tool_calls:
        return None
    tc = tool_calls[0]
    name = tc.get("function", {}).get("name")
    args = tc.get("function", {}).get("arguments")
    if isinstance(args, str):
        args = json.loads(args)
    return name, args
