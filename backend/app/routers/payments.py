"""
Razorpay payment router.

Flow:
  1. POST /payments/create-order  → create Razorpay order, return order_id + key_id
  2. Frontend opens Razorpay checkout widget with order_id
  3. User pays; Razorpay returns razorpay_payment_id, razorpay_order_id, razorpay_signature
  4. POST /payments/verify        → verify HMAC, confirm booking, send email
"""

import hashlib
import hmac
import json
import uuid
from datetime import datetime

import razorpay
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.config import settings
from app.core.deps import get_current_user
from app.db import get_session
from app.models import Booking, Payment, Showtime, User
from app.services.checkout import persist_booking
from app.services.email_service import send_booking_confirmation
from app.services.tickets import build_ticket
from app.services.websocket_manager import seat_ws_manager

router = APIRouter(prefix="/payments", tags=["payments"])

rzp_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class CreateOrderRequest(BaseModel):
    showtime_id: int
    seats: list[str]
    hold_token: str | None = None
    session_key: str | None = None


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    showtime_id: int
    seats: list[str]
    hold_token: str | None = None
    session_key: str | None = None


@router.post("/create-order")
def create_order(
    payload: CreateOrderRequest,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    showtime = session.exec(select(Showtime).where(Showtime.id == payload.showtime_id)).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")

    amount_inr = showtime.base_price * len(payload.seats)
    amount_paise = int(amount_inr * 100)

    idempotency_key = str(uuid.uuid4())
    try:
        order = rzp_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": idempotency_key,
            "notes": {
                "user_id": str(user.id),
                "showtime_id": str(payload.showtime_id),
                "seats": ",".join(payload.seats),
            },
        })
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Razorpay order creation failed: {e}")

    payment = Payment(
        user_id=user.id,
        provider="RAZORPAY",
        amount=amount_inr,
        currency="INR",
        status="INITIATED",
        idempotency_key=idempotency_key,
        provider_reference=order["id"],
    )
    session.add(payment)
    session.commit()

    return {
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key_id": settings.RAZORPAY_KEY_ID,
        "name": "Ticketly",
        "description": f"Movie tickets – {len(payload.seats)} seat(s)",
        "idempotency_key": idempotency_key,
    }


@router.post("/verify")
async def verify_payment(
    payload: VerifyPaymentRequest,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    # 1. Verify Razorpay signature (HMAC-SHA256)
    body = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, payload.razorpay_signature):
        raise HTTPException(status_code=400, detail="Payment signature verification failed")

    # 2. Saga: persist booking + confirm payment atomically
    try:
        booking = persist_booking(
            session,
            user_id=user.id,
            showtime_id=payload.showtime_id,
            seats=payload.seats,
            hold_token=payload.hold_token,
            session_key=payload.session_key,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Booking persistence failed: {e}")

    # 3. Update payment record to COMPLETED
    payment = session.exec(
        select(Payment).where(Payment.provider_reference == payload.razorpay_order_id)
    ).first()
    if payment:
        payment.booking_id = booking.id
        payment.status = "COMPLETED"
        payment.updated_at = datetime.utcnow()
        session.add(payment)
        session.commit()

    # 4. Broadcast seat update via WebSocket
    booked_seats = json.loads(booking.seats) if isinstance(booking.seats, str) else booking.seats
    await seat_ws_manager.broadcast(payload.showtime_id, {
        "type": "seats_booked",
        "showtime_id": payload.showtime_id,
        "seats": booked_seats,
    })

    # 5. Send email confirmation (async, non-blocking)
    try:
        ticket = build_ticket(session, booking.id)
        if user.email:
            import asyncio
            asyncio.create_task(send_booking_confirmation(user.email, ticket))
    except Exception:
        pass

    return {
        "status": "success",
        "booking_id": booking.id,
        "payment_id": payload.razorpay_payment_id,
        "booking": booking,
    }


@router.post("/refund/{booking_id}")
def refund_booking(
    booking_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    booking = session.exec(select(Booking).where(Booking.id == booking_id)).first()
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    payment = session.exec(
        select(Payment).where(Payment.booking_id == booking_id, Payment.status == "COMPLETED")
    ).first()
    if not payment:
        raise HTTPException(status_code=400, detail="No completed payment found for this booking")

    amount_paise = int(payment.amount * 100)
    try:
        rzp_client.payment.refund(payment.provider_reference, {"amount": amount_paise})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Refund failed: {e}")

    payment.status = "REFUNDED"
    payment.updated_at = datetime.utcnow()
    booking.status = "CANCELLED"
    session.add(payment)
    session.add(booking)
    session.commit()

    return {"booking_id": booking_id, "refund_status": "REFUNDED", "amount": payment.amount}
