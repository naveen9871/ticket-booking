from sqlmodel import Session, select

from app.models import Movie, Booking, Showtime


def recommend_movies(session: Session, user_id: int | None = None) -> list[Movie]:
    query = select(Movie)
    
    if user_id:
        user = session.get(User, user_id)
        if user and user.genre_preferences:
            genres = [g.strip().lower() for g in user.genre_preferences.split(",")]
            # Match any of the preferred genres
            from sqlalchemy import or_
            query = query.where(or_(*[Movie.genre.ilike(f"%{g}%") for g in genres]))
            
        # Also consider past bookings if no genre prefs or as extra weights
        # For simplicity, we just boost high-rated movies in preferred genres
        
    return session.exec(query.order_by(Movie.rating.desc()).limit(10)).all()
