"""
Ticket Transfer & Waitlist API endpoints (Section 6.7).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.deps import get_current_user
from app.db import get_session
from app.models import User
from app.services.transfer import (
    accept_transfer_offer,
    cancel_transfer_listing,
    get_active_transfers_for_showtime,
    get_waitlist_for_showtime,
    join_waitlist,
    leave_waitlist,
    list_transfer,
    run_matching_for_transfer,
    run_transfer_expiry_cycle,
)

router = APIRouter(prefix="/transfers", tags=["transfers"])


class ListTransferRequest(BaseModel):
    booking_id: int


class JoinWaitlistRequest(BaseModel):
    showtime_id: int
    party_size: int = Field(default=2, ge=1, le=10)
    price_ceiling: float | None = None


class AcceptOfferRequest(BaseModel):
    transfer_id: int


# ---------------------------------------------------------------------------
# Transfer pool
# ---------------------------------------------------------------------------

@router.post("")
def create_transfer(
    payload: ListTransferRequest,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Seller lists a booking for transfer at face value."""
    try:
        transfer = list_transfer(session, payload.booking_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "transfer_id": transfer.id,
        "showtime_id": transfer.showtime_id,
        "face_value": transfer.face_value,
        "expires_at": transfer.expires_at.isoformat(),
        "status": transfer.status,
        "message": "Ticket listed for transfer. Buyers in the waitlist will be offered your ticket.",
    }


@router.delete("/{transfer_id}")
def cancel_transfer(
    transfer_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        transfer = cancel_transfer_listing(session, transfer_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"transfer_id": transfer.id, "status": transfer.status}


@router.get("/showtime/{showtime_id}")
def list_transfers_for_showtime(
    showtime_id: int,
    session: Session = Depends(get_session),
):
    transfers = get_active_transfers_for_showtime(session, showtime_id)
    return {"showtime_id": showtime_id, "count": len(transfers), "transfers": transfers}


@router.post("/{transfer_id}/match")
def trigger_match(
    transfer_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Admin / system endpoint to run matching for a specific transfer."""
    result = run_matching_for_transfer(session, transfer_id)
    return result


@router.post("/{transfer_id}/accept")
def accept_offer(
    transfer_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Buyer accepts a transfer offer within the 5-minute window."""
    try:
        result = accept_transfer_offer(session, transfer_id, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


# ---------------------------------------------------------------------------
# Waitlist
# ---------------------------------------------------------------------------

@router.post("/waitlist")
def join_showtime_waitlist(
    payload: JoinWaitlistRequest,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Join the FIFO waitlist for a sold-out showtime."""
    entry = join_waitlist(
        session,
        user_id=user.id,
        showtime_id=payload.showtime_id,
        party_size=payload.party_size,
        price_ceiling=payload.price_ceiling,
    )
    return {
        "waitlist_id": entry.id,
        "showtime_id": entry.showtime_id,
        "queue_position": entry.queue_position,
        "status": entry.status,
        "message": f"You are #{entry.queue_position} in the queue. We'll notify you when a ticket becomes available.",
    }


@router.delete("/waitlist/{showtime_id}")
def leave_showtime_waitlist(
    showtime_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        result = leave_waitlist(session, user.id, showtime_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.get("/waitlist/showtime/{showtime_id}")
def get_showtime_waitlist(
    showtime_id: int,
    session: Session = Depends(get_session),
):
    entries = get_waitlist_for_showtime(session, showtime_id)
    return {"showtime_id": showtime_id, "queue_length": len(entries), "entries": entries}


# ---------------------------------------------------------------------------
# Admin / scheduler
# ---------------------------------------------------------------------------

@router.post("/admin/run-expiry-cycle")
def run_expiry_cycle(session: Session = Depends(get_session)):
    """Run the transfer expiry & re-offer cycle (called by scheduler)."""
    return run_transfer_expiry_cycle(session)
