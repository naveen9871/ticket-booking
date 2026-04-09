import json

from sqlmodel import Session, select

from app.models import Screen, Showtime, Booking


def get_seat_map(session: Session, showtime_id: int) -> list[list[dict]]:
    showtime = session.exec(select(Showtime).where(Showtime.id == showtime_id)).first()
    if not showtime:
        return []
    screen = session.exec(select(Screen).where(Screen.id == showtime.screen_id)).first()
    if not screen:
        return []
    seat_map = json.loads(screen.seat_map)

    bookings = session.exec(select(Booking).where(Booking.showtime_id == showtime_id)).all()
    booked = set()
    for b in bookings:
        for seat in json.loads(b.seats):
            booked.add(seat)

    for row in seat_map:
        for seat in row:
            if seat["id"] in booked:
                seat["status"] = "BOOKED"
    return seat_map


def auto_select_seats(seat_map: list[list[dict]], count: int) -> list[str]:
    if count <= 0 or not seat_map:
        return []

    num_rows = len(seat_map)
    middle_row = num_rows // 2
    
    best_seats = []
    min_distance_from_center = float("inf")

    for r_idx, row in enumerate(seat_map):
        num_cols = len(row)
        middle_col = num_cols // 2
        
        # Look for contiguous available seats in this row
        for i in range(len(row) - count + 1):
            block = row[i : i + count]
            if all(s["status"] == "AVAILABLE" for s in block):
                # Calculate "center bias" score
                block_center = i + (count / 2)
                row_dist = abs(r_idx - middle_row)
                col_dist = abs(block_center - middle_col)
                score = row_dist + col_dist # Taxicab distance to center
                
                if score < min_distance_from_center:
                    min_distance_from_center = score
                    best_seats = [s["id"] for s in block]

    return best_seats
