from datetime import datetime

from sqlmodel import Session, select

from app.models import Showtime, Booking


def compute_dynamic_price(session: Session, showtime_id: int, base_price: float) -> dict:
    showtime = session.exec(select(Showtime).where(Showtime.id == showtime_id)).first()
    if not showtime:
        return {"price": base_price, "surge": 1.0, "reason": "unknown showtime"}

    # Simulate occupancy if no actual bookings for demo
    bookings = session.exec(select(Booking).where(Booking.showtime_id == showtime_id)).all()
    num_bookings = len(bookings)
    occupancy = min(num_bookings / 50, 1.0) # Assume 50 capacity for demo surge logic
    
    now = datetime.utcnow()
    hours_to_show = max((showtime.start_time - now).total_seconds() / 3600, 0)

    surge = 1.0
    reasons = []

    if occupancy > 0.6:
        surge += 0.2
        reasons.append("high demand")
    if hours_to_show < 4:
        surge += 0.15
        reasons.append("last minute")
    
    # Weekend surge (Friday evening to Sunday)
    if showtime.start_time.weekday() >= 4: # 4 is Friday
        surge += 0.1
        reasons.append("weekend")
        
    # Peak hour surge (6 PM to 10 PM)
    if 18 <= showtime.start_time.hour <= 22:
        surge += 0.1
        reasons.append("peak hour")

    price = round(base_price * surge, 2)
    return {"price": price, "surge": round(surge, 2), "reason": ", ".join(reasons) or "base"}
