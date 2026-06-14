"""
Ticket Transfer & Waitlist service (Section 6.7).

Workflow:
  Seller lists booking → enters transfer pool with TTL
  Buyers join FIFO waitlist for that showtime
  Matching Agent offers ticket to next-in-queue (5-min acceptance window)
  On acceptance: atomic cancel seller's booking → rebook for buyer
  On timeout/rejection: offer to next in queue
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from sqlmodel import Session, select

from app.models import (
    Booking,
    Notification,
    SeatHold,
    TicketTransfer,
    Waitlist,
)
from app.services.checkout import persist_booking
from app.services.seats import create_seat_hold

TRANSFER_POOL_TTL_HOURS = 24
ACCEPTANCE_WINDOW_MINUTES = 5


# ---------------------------------------------------------------------------
# Transfer pool helpers
# ---------------------------------------------------------------------------

def list_transfer(
    session: Session,
    booking_id: int,
    seller_user_id: int,
) -> TicketTransfer:
    booking = session.get(Booking, booking_id)
    if not booking:
        raise ValueError("Booking not found")
    if booking.user_id != seller_user_id:
        raise ValueError("Not your booking")
    if booking.status != "CONFIRMED":
        raise ValueError("Only confirmed bookings can be transferred")

    existing = session.exec(
        select(TicketTransfer).where(
            TicketTransfer.booking_id == booking_id,
            TicketTransfer.status == "LISTED",
        )
    ).first()
    if existing:
        return existing

    transfer = TicketTransfer(
        booking_id=booking_id,
        seller_user_id=seller_user_id,
        showtime_id=booking.showtime_id,
        seats=booking.seats,
        face_value=booking.total_price,
        status="LISTED",
        expires_at=datetime.utcnow() + timedelta(hours=TRANSFER_POOL_TTL_HOURS),
    )
    session.add(transfer)
    session.commit()
    session.refresh(transfer)
    return transfer


def cancel_transfer_listing(session: Session, transfer_id: int, seller_user_id: int) -> TicketTransfer:
    transfer = session.get(TicketTransfer, transfer_id)
    if not transfer or transfer.seller_user_id != seller_user_id:
        raise ValueError("Transfer not found")
    if transfer.status not in ("LISTED",):
        raise ValueError("Cannot cancel a transfer that is not listed")
    transfer.status = "CANCELLED"
    transfer.updated_at = datetime.utcnow()
    session.add(transfer)
    session.commit()
    session.refresh(transfer)
    return transfer


def get_active_transfers_for_showtime(session: Session, showtime_id: int) -> list[TicketTransfer]:
    now = datetime.utcnow()
    return list(
        session.exec(
            select(TicketTransfer).where(
                TicketTransfer.showtime_id == showtime_id,
                TicketTransfer.status == "LISTED",
                TicketTransfer.expires_at > now,
            )
        ).all()
    )


# ---------------------------------------------------------------------------
# Waitlist helpers
# ---------------------------------------------------------------------------

def join_waitlist(
    session: Session,
    user_id: int,
    showtime_id: int,
    party_size: int = 2,
    price_ceiling: float | None = None,
) -> Waitlist:
    existing = session.exec(
        select(Waitlist).where(
            Waitlist.user_id == user_id,
            Waitlist.showtime_id == showtime_id,
            Waitlist.status.in_(("WAITING", "OFFERED")),
        )
    ).first()
    if existing:
        return existing

    # Assign next FIFO position
    last = session.exec(
        select(Waitlist)
        .where(
            Waitlist.showtime_id == showtime_id,
            Waitlist.status.in_(("WAITING", "OFFERED")),
        )
        .order_by(Waitlist.queue_position.desc())  # type: ignore[arg-type]
    ).first()
    position = (last.queue_position + 1) if last else 1

    entry = Waitlist(
        user_id=user_id,
        showtime_id=showtime_id,
        party_size=party_size,
        price_ceiling=price_ceiling,
        status="WAITING",
        queue_position=position,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def leave_waitlist(session: Session, user_id: int, showtime_id: int) -> dict[str, Any]:
    entry = session.exec(
        select(Waitlist).where(
            Waitlist.user_id == user_id,
            Waitlist.showtime_id == showtime_id,
            Waitlist.status.in_(("WAITING", "OFFERED")),
        )
    ).first()
    if not entry:
        raise ValueError("Not on waitlist")
    entry.status = "CANCELLED"
    entry.updated_at = datetime.utcnow()
    session.add(entry)
    session.commit()
    return {"cancelled": True, "position": entry.queue_position}


def get_waitlist_for_showtime(session: Session, showtime_id: int) -> list[Waitlist]:
    return list(
        session.exec(
            select(Waitlist)
            .where(
                Waitlist.showtime_id == showtime_id,
                Waitlist.status.in_(("WAITING",)),
            )
            .order_by(Waitlist.queue_position)  # type: ignore[arg-type]
        ).all()
    )


# ---------------------------------------------------------------------------
# Matching Agent — offer ticket to next buyer in queue
# ---------------------------------------------------------------------------

def _notify(session: Session, user_id: int, title: str, message: str, metadata: dict | None = None) -> None:
    n = Notification(
        user_id=user_id,
        channel="PUSH",
        title=title,
        message=message,
        status="QUEUED",
        metadata_json=json.dumps(metadata or {}),
    )
    session.add(n)


def run_matching_for_transfer(session: Session, transfer_id: int) -> dict[str, Any]:
    """
    Offer the transfer to the next WAITING buyer.
    Returns {status, buyer_id, offer_expires_at} or {status: "no_buyers"}.
    """
    transfer = session.get(TicketTransfer, transfer_id)
    if not transfer or transfer.status != "LISTED":
        return {"status": "invalid_transfer"}

    queue = get_waitlist_for_showtime(session, transfer.showtime_id)
    if not queue:
        return {"status": "no_buyers"}

    buyer_entry = queue[0]  # FIFO — head of queue
    deadline = datetime.utcnow() + timedelta(minutes=ACCEPTANCE_WINDOW_MINUTES)

    # Mark transfer as MATCHED with buyer
    transfer.status = "MATCHED"
    transfer.matched_buyer_id = buyer_entry.user_id
    transfer.acceptance_deadline = deadline
    transfer.updated_at = datetime.utcnow()
    session.add(transfer)

    # Mark buyer waitlist entry as OFFERED
    buyer_entry.status = "OFFERED"
    buyer_entry.offer_expires_at = deadline
    buyer_entry.updated_at = datetime.utcnow()
    session.add(buyer_entry)

    _notify(
        session,
        buyer_entry.user_id,
        "Ticket available!",
        f"A ticket for showtime #{transfer.showtime_id} is available at ₹{transfer.face_value:.0f}. "
        f"Accept within {ACCEPTANCE_WINDOW_MINUTES} minutes.",
        {"transfer_id": transfer.id, "accept_before": deadline.isoformat()},
    )
    session.commit()

    return {
        "status": "offered",
        "buyer_id": buyer_entry.user_id,
        "offer_expires_at": deadline.isoformat(),
        "transfer_id": transfer.id,
    }


def accept_transfer_offer(
    session: Session,
    transfer_id: int,
    buyer_user_id: int,
) -> dict[str, Any]:
    """
    Atomic cancel-and-rebook:
      1. Verify acceptance window is open
      2. Cancel seller's booking
      3. Hold seats immediately for buyer
      4. Create new booking for buyer
      5. Notify both parties
    """
    transfer = session.get(TicketTransfer, transfer_id)
    if not transfer:
        raise ValueError("Transfer not found")
    if transfer.status != "MATCHED":
        raise ValueError("Transfer is not in an offered state")
    if transfer.matched_buyer_id != buyer_user_id:
        raise ValueError("This offer was not made to you")
    if transfer.acceptance_deadline and datetime.utcnow() > transfer.acceptance_deadline:
        _expire_offer(session, transfer)
        raise ValueError("Acceptance window has expired")

    # 1. Cancel seller's booking
    seller_booking = session.get(Booking, transfer.booking_id)
    if not seller_booking:
        raise ValueError("Original booking not found")
    seller_booking.status = "CANCELLED"
    session.add(seller_booking)

    # 2. Release any seat holds for seller
    holds = session.exec(
        select(SeatHold).where(
            SeatHold.showtime_id == transfer.showtime_id,
            SeatHold.user_id == transfer.seller_user_id,
            SeatHold.status == "CONFIRMED",
        )
    ).all()
    for hold in holds:
        hold.status = "RELEASED"
        session.add(hold)

    # 3. Create new booking for buyer at face value
    seats = json.loads(transfer.seats)
    new_booking = Booking(
        user_id=buyer_user_id,
        showtime_id=transfer.showtime_id,
        seats=transfer.seats,
        total_price=transfer.face_value,
        status="CONFIRMED",
    )
    session.add(new_booking)
    session.flush()

    # 4. Mark transfer COMPLETED
    transfer.status = "COMPLETED"
    transfer.updated_at = datetime.utcnow()
    session.add(transfer)

    # 5. Mark buyer waitlist entry ACCEPTED
    waitlist_entry = session.exec(
        select(Waitlist).where(
            Waitlist.user_id == buyer_user_id,
            Waitlist.showtime_id == transfer.showtime_id,
            Waitlist.status == "OFFERED",
        )
    ).first()
    if waitlist_entry:
        waitlist_entry.status = "ACCEPTED"
        waitlist_entry.updated_at = datetime.utcnow()
        session.add(waitlist_entry)

    # 6. Notify both parties
    _notify(
        session,
        transfer.seller_user_id,
        "Ticket transferred",
        f"Your ticket for showtime #{transfer.showtime_id} has been successfully transferred at ₹{transfer.face_value:.0f}.",
        {"new_booking_id": new_booking.id},
    )
    _notify(
        session,
        buyer_user_id,
        "Booking confirmed via transfer",
        f"You have successfully received the ticket for showtime #{transfer.showtime_id}. Seats: {', '.join(seats)}.",
        {"booking_id": new_booking.id},
    )

    session.commit()
    session.refresh(new_booking)

    return {
        "status": "completed",
        "new_booking_id": new_booking.id,
        "seats": seats,
        "price": transfer.face_value,
        "showtime_id": transfer.showtime_id,
    }


def _expire_offer(session: Session, transfer: TicketTransfer) -> None:
    """Revert a MATCHED transfer back to LISTED and expire the buyer's OFFERED entry."""
    transfer.status = "LISTED"
    transfer.matched_buyer_id = None
    transfer.acceptance_deadline = None
    transfer.updated_at = datetime.utcnow()
    session.add(transfer)

    entry = session.exec(
        select(Waitlist).where(
            Waitlist.showtime_id == transfer.showtime_id,
            Waitlist.status == "OFFERED",
        )
    ).first()
    if entry:
        entry.status = "EXPIRED"
        entry.updated_at = datetime.utcnow()
        session.add(entry)

    session.commit()


def run_transfer_expiry_cycle(session: Session) -> dict[str, Any]:
    """
    Cron-style cycle:
      - Expire acceptance windows → re-offer to next buyer
      - Expire stale LISTED transfers past their TTL
    """
    now = datetime.utcnow()
    expired_offers = 0
    re_offered = 0
    expired_listings = 0

    # Expire acceptance windows past deadline
    matched = session.exec(
        select(TicketTransfer).where(
            TicketTransfer.status == "MATCHED",
            TicketTransfer.acceptance_deadline < now,
        )
    ).all()
    for transfer in matched:
        _expire_offer(session, transfer)
        expired_offers += 1
        # Try next buyer
        result = run_matching_for_transfer(session, transfer.id)
        if result.get("status") == "offered":
            re_offered += 1

    # Expire listings past their pool TTL
    old_listings = session.exec(
        select(TicketTransfer).where(
            TicketTransfer.status == "LISTED",
            TicketTransfer.expires_at < now,
        )
    ).all()
    for transfer in old_listings:
        transfer.status = "EXPIRED"
        transfer.updated_at = now
        session.add(transfer)
        expired_listings += 1

    session.commit()
    return {
        "expired_offers": expired_offers,
        "re_offered": re_offered,
        "expired_listings": expired_listings,
    }
