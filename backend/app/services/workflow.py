import json
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models import AgentSession, EventPlan, WorkflowEvent


def create_agent_session(
    session: Session,
    session_key: str,
    user_id: int | None,
    workflow_type: str,
    context: dict[str, Any] | None = None,
) -> AgentSession:
    agent_session = AgentSession(
        user_id=user_id,
        session_key=session_key,
        workflow_type=workflow_type,
        context_json=json.dumps(context or {}),
    )
    session.add(agent_session)
    session.commit()
    session.refresh(agent_session)
    return agent_session


def update_agent_session(
    session: Session,
    agent_session: AgentSession,
    *,
    status: str | None = None,
    current_stage: str | None = None,
    context: dict[str, Any] | None = None,
    last_error: str | None = None,
) -> AgentSession:
    if status:
        agent_session.status = status
    if current_stage:
        agent_session.current_stage = current_stage
    if context is not None:
        agent_session.context_json = json.dumps(context)
    if last_error is not None:
        agent_session.last_error = last_error
    agent_session.updated_at = datetime.utcnow()
    session.add(agent_session)
    session.commit()
    session.refresh(agent_session)
    return agent_session


def log_workflow_event(
    session: Session,
    agent_session_id: int,
    agent_name: str,
    event_type: str,
    status: str,
    payload: dict[str, Any] | None = None,
) -> WorkflowEvent:
    event = WorkflowEvent(
        agent_session_id=agent_session_id,
        agent_name=agent_name,
        event_type=event_type,
        status=status,
        payload_json=json.dumps(payload or {}),
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def replace_plans(session: Session, agent_session_id: int, plans: list[dict[str, Any]]) -> list[EventPlan]:
    existing = session.exec(select(EventPlan).where(EventPlan.agent_session_id == agent_session_id)).all()
    for plan in existing:
        session.delete(plan)
    session.commit()

    saved_plans: list[EventPlan] = []
    for idx, plan in enumerate(plans, start=1):
        row = EventPlan(
            agent_session_id=agent_session_id,
            rank=idx,
            title=plan["title"],
            summary=plan["summary"],
            plan_type=plan.get("plan_type", "BALANCED"),
            confidence=plan.get("confidence", 0.0),
            showtime_id=plan.get("showtime_id"),
            theatre_id=plan.get("theatre_id"),
            seats_json=json.dumps(plan.get("seats", [])),
            estimated_total=plan.get("estimated_total", 0.0),
            rationale_json=json.dumps(plan.get("rationale", [])),
            metadata_json=json.dumps(plan.get("metadata", {})),
        )
        session.add(row)
        saved_plans.append(row)

    session.commit()
    for plan in saved_plans:
        session.refresh(plan)
    return saved_plans
