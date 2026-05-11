from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlmodel import Session

from app.services.discovery import discover_showtimes
from app.services.intent import parse_intent
from app.services.planning import generate_plans
from app.services.preferences import get_or_create_memory, load_profile, update_memory_from_intent
from app.services.recovery import build_recovery_message, normalize_failure
from app.services.workflow import (
    create_agent_session,
    log_workflow_event,
    replace_plans,
    update_agent_session,
)


def ensure_session_key(context: dict[str, Any] | None) -> str:
    context = context or {}
    session_key = context.get("session_key")
    if session_key:
        return session_key
    return f"guest-{uuid4().hex[:12]}"


def run_agentic_planning(
    session: Session,
    user_id: int | None,
    message: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = context or {}
    session_key = ensure_session_key(context)
    memory = get_or_create_memory(session, session_key, user_id)
    profile = load_profile(memory)
    agent_session = create_agent_session(
        session,
        session_key=session_key,
        user_id=user_id,
        workflow_type="EVENT_BOOKING",
        context=context,
    )

    trace: list[dict[str, str]] = []

    try:
        log_workflow_event(session, agent_session.id, "intent-agent", "INTENT_PARSE_STARTED", "RUNNING")
        intent = parse_intent(session, message, context=context, profile=profile)
        update_memory_from_intent(session, memory, intent, message)
        trace.append({"agent": "Intent Agent", "status": "done", "detail": intent["summary"]})
        log_workflow_event(session, agent_session.id, "intent-agent", "INTENT_PARSE_COMPLETED", "COMPLETED", intent)
        update_agent_session(session, agent_session, status="RUNNING", current_stage="DISCOVERY", context={**context, "intent": intent})

        log_workflow_event(session, agent_session.id, "discovery-agent", "DISCOVERY_STARTED", "RUNNING")
        candidates = discover_showtimes(session, intent)
        trace.append({"agent": "Discovery Agent", "status": "done", "detail": f"Found {len(candidates)} candidate showtimes."})
        log_workflow_event(session, agent_session.id, "discovery-agent", "DISCOVERY_COMPLETED", "COMPLETED", {"count": len(candidates)})
        update_agent_session(session, agent_session, current_stage="PLANNING")

        if not candidates:
            update_agent_session(session, agent_session, status="FAILED", last_error="No matching inventory")
            trace.append({"agent": "Recovery Agent", "status": "done", "detail": "Prepared a fallback prompt for broader search."})
            return {
                **build_recovery_message(intent, "no matching shows were available"),
                "context": {"session_key": session_key, "city": intent.get("city"), "seat_count": intent.get("party_size", 2)},
                "trace": trace,
            }

        log_workflow_event(session, agent_session.id, "planning-agent", "PLANNING_STARTED", "RUNNING")
        plans = generate_plans(session, intent, candidates)
        saved_plans = replace_plans(session, agent_session.id, plans)
        trace.append({"agent": "Planning Agent", "status": "done", "detail": f"Prepared {len(saved_plans)} plan options."})
        log_workflow_event(session, agent_session.id, "planning-agent", "PLANNING_COMPLETED", "COMPLETED", {"plans": len(saved_plans)})
        update_agent_session(
            session,
            agent_session,
            status="AWAITING_USER",
            current_stage="APPROVAL",
            context={**context, "intent": intent, "plans": [plan.id for plan in saved_plans]},
        )

        return {
            "type": "agent_plan",
            "message": "I built three booking strategies so you can choose speed, value, or a more premium experience.",
            "data": {
                "intent": intent,
                "plans": plans,
                "top_candidates": candidates[:6],
            },
            "context": {
                "session_key": session_key,
                "city": intent.get("city"),
                "seat_count": intent.get("party_size", 2),
                "intent_kind": intent.get("kind"),
            },
            "trace": trace,
        }
    except Exception as exc:
        error_text = normalize_failure(exc)
        update_agent_session(session, agent_session, status="FAILED", current_stage="RECOVERY", last_error=error_text)
        log_workflow_event(session, agent_session.id, "recovery-agent", "WORKFLOW_FAILED", "FAILED", {"error": error_text})
        trace.append({"agent": "Recovery Agent", "status": "done", "detail": "Captured the failure and prepared a safe fallback."})
        fallback_intent = context.get("intent") or {}
        return {
            **build_recovery_message(fallback_intent, error_text),
            "context": {"session_key": session_key, "city": fallback_intent.get("city"), "seat_count": fallback_intent.get("party_size", 2)},
            "trace": trace,
        }
