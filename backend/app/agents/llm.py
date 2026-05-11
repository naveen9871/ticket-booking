import json
from typing import Any

import httpx
import google.generativeai as genai
from app.core.config import settings

def call_llm(messages: list[dict], tools: list[dict] | None = None) -> dict[str, Any] | None:
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "openai":
        return _call_openai(messages, tools)
    elif provider == "gemini":
        return _call_gemini(messages, tools)
    else:
        # Fallback to whatever key is available
        if settings.GEMINI_API_KEY:
            return _call_gemini(messages, tools)
        return _call_openai(messages, tools)

def _call_openai(messages: list[dict], tools: list[dict] | None = None) -> dict[str, Any] | None:
    if not settings.OPENAI_API_KEY:
        return None

    url = "https://api.openai.com/v1/chat/completions"
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

    try:
        with httpx.Client(timeout=25) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return None

def _call_gemini(messages: list[dict], tools: list[dict] | None = None) -> dict[str, Any] | None:
    if not settings.GEMINI_API_KEY:
        return None

    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    system_instruction = None
    contents = []
    for m in messages:
        if m["role"] == "system":
            system_instruction = m["content"]
        else:
            role = "user" if m["role"] == "user" else "model"
            contents.append({"role": role, "parts": [m["content"]]})

    # Convert OpenAI tools to Gemini tools
    gemini_tools = None
    if tools:
        # Simplistic conversion to avoid proto-plus KeyError: 'object'
        # We only pass the function name and description if the schema is complex
        # Or we rely on the SDK's automatic conversion if possible
        try:
            gemini_tools = [t["function"] for t in tools if t["type"] == "function"]
        except Exception:
            gemini_tools = None

    try:
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            tools=gemini_tools,
            system_instruction=system_instruction
        )
        
        # Use generate_content instead of start_chat for the direct request
        response = model.generate_content(contents)
        
        content = ""
        tool_calls = []
        if response.candidates:
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if part.text:
                    content += part.text
                if part.function_call:
                    fn = part.function_call
                    tool_calls.append({
                        "function": {
                            "name": fn.name,
                            "arguments": json.dumps({k: v for k, v in fn.args.items()})
                        }
                    })

        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_calls if tool_calls else None
                }
            }]
        }
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        # Final fallback: no tools, no system instruction if needed
        try:
            model = genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
            # Combine everything into one prompt for the fallback
            prompt = ""
            if system_instruction:
                prompt += f"System: {system_instruction}\n\n"
            for c in contents:
                prompt += f"{c['role']}: {c['parts'][0]}\n"
            
            response = model.generate_content(prompt)
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response.text,
                        "tool_calls": None
                    }
                }]
            }
        except Exception as e2:
            print(f"Critical error calling Gemini fallback: {e2}")
            return None


def extract_tool_call(response: dict[str, Any] | None) -> tuple[str, dict] | None:
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
