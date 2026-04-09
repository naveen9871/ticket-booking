import json
from typing import Any

import httpx

from app.core.config import settings

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def call_llm(messages: list[dict], tools: list[dict] | None = None) -> dict[str, Any] | None:
    if not settings.OPENAI_API_KEY:
        return None

    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": messages,
        "temperature": 0.3,
    }
    if tools:
        payload["tools"] = tools

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=20) as client:
        resp = client.post(OPENAI_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


def extract_tool_call(response: dict[str, Any]) -> tuple[str, dict] | None:
    if not response:
        return None
    choices = response.get("choices", [])
    if not choices:
        return None
    msg = choices[0].get("message", {})
    tool_calls = msg.get("tool_calls") or []
    if not tool_calls:
        return None
    tool_call = tool_calls[0]
    name = tool_call.get("function", {}).get("name")
    args = tool_call.get("function", {}).get("arguments")
    if isinstance(args, str):
        args = json.loads(args)
    return name, args
