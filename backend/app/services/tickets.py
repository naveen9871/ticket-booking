import base64
import io
from typing import Any

import qrcode
from sqlmodel import Session, select

from app.models import Booking, Showtime, Screen, Theatre, Movie


def build_ticket(session: Session, booking_id: int) -> dict[str, Any] | None:
    booking = session.exec(select(Booking).where(Booking.id == booking_id)).first()
    if not booking:
        return None
    showtime = session.exec(select(Showtime).where(Showtime.id == booking.showtime_id)).first()
    if not showtime:
        return None
    screen = session.exec(select(Screen).where(Screen.id == showtime.screen_id)).first()
    theatre = session.exec(select(Theatre).where(Theatre.id == screen.theatre_id)).first() if screen else None
    movie = session.exec(select(Movie).where(Movie.id == showtime.movie_id)).first()

    payload = {
        "booking_id": booking.id,
        "showtime_id": showtime.id,
        "movie": movie.title if movie else None,
        "theatre": theatre.name if theatre else None,
        "city": theatre.city if theatre else None,
        "screen": screen.name if screen else None,
        "start_time": showtime.start_time.isoformat(),
        "seats": booking.seats,
        "total_price": booking.total_price,
    }

    qr_text = (
        f"BOOKING:{booking.id}|SHOW:{showtime.id}|MOVIE:{movie.title if movie else ''}|"
        f"THEATRE:{theatre.name if theatre else ''}|SEATS:{booking.seats}"
    )
    img = qrcode.make(qr_text)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "ticket": payload,
        "qr": f"data:image/png;base64,{qr_base64}",
    }
