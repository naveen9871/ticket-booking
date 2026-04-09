from sqlmodel import Session, select

from app.models import Movie, Theatre, Showtime


def search_catalog(session: Session, query: str) -> dict:
    q = f"%{query.lower()}%"
    # Basic keyword extraction for city/genre/title
    words = query.lower().split()
    
    movie_query = select(Movie).where(Movie.title.ilike(q) | Movie.genre.ilike(q) | Movie.tags.ilike(q))
    movies = session.exec(movie_query).all()
    
    theatre_query = select(Theatre).where(Theatre.name.ilike(q) | Theatre.city.ilike(q))
    theatres = session.exec(theatre_query).all()
    
    movie_ids = [m.id for m in movies]
    theatre_ids = [t.id for t in theatres]
    
    showtime_query = select(Showtime)
    if movie_ids or theatre_ids:
        # If we found specific movies/theatres, find showtimes for them
        conditions = []
        if movie_ids:
            conditions.append(Showtime.movie_id.in_(movie_ids))
        if theatre_ids:
            # Also need to link theatre -> screen -> showtime or just search screens in theatre
            # For simplicity, we filter by movie_id and maybe theatre city separately
            pass
        
        if conditions:
            showtime_query = showtime_query.where(conditions[0]) # Simplified
            
    showtimes = session.exec(showtime_query.limit(20)).all()
    
    return {
        "movies": movies,
        "theatres": theatres,
        "showtimes": showtimes,
    }
