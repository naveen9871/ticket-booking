from datetime import datetime, timedelta
import json
import random

from sqlmodel import Session, select

from app.models import Movie, Theatre, Screen, Showtime


def build_seat_map(rows: int = 10, cols: int = 16) -> str:
    seat_map = []
    for r in range(rows):
        row_label = chr(65 + r)
        row = []
        for c in range(1, cols + 1):
            row.append({"id": f"{row_label}{c}", "type": "STANDARD", "status": "AVAILABLE"})
        seat_map.append(row)
    return json.dumps(seat_map)


DEFAULT_POSTER = "https://images.unsplash.com/photo-1489515217757-5fd1be406fef"


def _get_movie_by_title(session: Session, title: str) -> Movie | None:
    return session.exec(select(Movie).where(Movie.title == title)).first()


def _get_theatre_by_name_city(session: Session, name: str, city: str) -> Theatre | None:
    return session.exec(select(Theatre).where(Theatre.name == name, Theatre.city == city)).first()


def seed_data(session: Session) -> None:

    movies = [
        Movie(title="Baahubali: The Beginning", description="An epic saga of rivalry and redemption in the kingdom of Mahishmati.", genre="Action", language="Telugu", duration_mins=159, rating=4.8, poster_url=DEFAULT_POSTER, tags="epic"),
        Movie(title="Baahubali 2: The Conclusion", description="The battle for Mahishmati reaches its legendary conclusion.", genre="Action", language="Telugu", duration_mins=167, rating=4.9, poster_url=DEFAULT_POSTER, tags="epic"),
        Movie(title="RRR", description="Two revolutionaries rise against the British empire in a breathtaking saga.", genre="Action", language="Telugu", duration_mins=187, rating=4.9, poster_url=DEFAULT_POSTER, tags="epic"),
        Movie(title="Salaar", description="A violent clash of brotherhood and power in a dystopian empire.", genre="Action", language="Telugu", duration_mins=175, rating=4.5, poster_url=DEFAULT_POSTER, tags="mass"),
        Movie(title="Pushpa: The Rise", description="A red sanders smuggler rises in the underworld.", genre="Action", language="Telugu", duration_mins=179, rating=4.4, poster_url=DEFAULT_POSTER, tags="mass"),
        Movie(title="Pushpa 2", description="The rule of Pushpa intensifies as enemies close in.", genre="Action", language="Telugu", duration_mins=180, rating=4.6, poster_url=DEFAULT_POSTER, tags="mass"),
        Movie(title="Devara", description="A fierce rivalry erupts along the coast.", genre="Action", language="Telugu", duration_mins=165, rating=4.3, poster_url=DEFAULT_POSTER, tags="action"),
        Movie(title="Arjun Reddy", description="A brilliant surgeon battles inner demons after heartbreak.", genre="Drama", language="Telugu", duration_mins=182, rating=4.5, poster_url=DEFAULT_POSTER, tags="romance"),
        Movie(title="Jailer", description="A retired jailer confronts a criminal network.", genre="Action", language="Tamil", duration_mins=168, rating=4.6, poster_url=DEFAULT_POSTER, tags="superstar"),
        Movie(title="Coolie", description="A gritty tale of a coolie caught in a power struggle.", genre="Action", language="Tamil", duration_mins=160, rating=4.4, poster_url=DEFAULT_POSTER, tags="rajini"),
        Movie(title="Vikram", description="A covert team races to stop a deadly drug syndicate.", genre="Action", language="Tamil", duration_mins=173, rating=4.7, poster_url=DEFAULT_POSTER, tags="lokesh"),
        Movie(title="Leo", description="A cafe owner is forced to confront his past.", genre="Action", language="Tamil", duration_mins=164, rating=4.3, poster_url=DEFAULT_POSTER, tags="thalapathy"),
        Movie(title="Master", description="A professor takes on a ruthless gangster.", genre="Action", language="Tamil", duration_mins=179, rating=4.4, poster_url=DEFAULT_POSTER, tags="vijay"),
        Movie(title="Kaithi", description="A convict faces one night of chaos to save his daughter.", genre="Action", language="Tamil", duration_mins=145, rating=4.7, poster_url=DEFAULT_POSTER, tags="thriller"),
        Movie(title="Pathaan", description="A spy returns to stop a global threat.", genre="Action", language="Hindi", duration_mins=146, rating=4.3, poster_url=DEFAULT_POSTER, tags="spy"),
        Movie(title="Jawan", description="A vigilante takes on a system gone wrong.", genre="Action", language="Hindi", duration_mins=169, rating=4.5, poster_url=DEFAULT_POSTER, tags="mass"),
        Movie(title="Dangal", description="A former wrestler trains his daughters for glory.", genre="Drama", language="Hindi", duration_mins=161, rating=4.8, poster_url=DEFAULT_POSTER, tags="sports"),
        Movie(title="3 Idiots", description="Three friends navigate life at an elite college.", genre="Drama", language="Hindi", duration_mins=170, rating=4.9, poster_url=DEFAULT_POSTER, tags="comedy"),
        Movie(title="KGF Chapter 1", description="The rise of Rocky in the Kolar Gold Fields.", genre="Action", language="Kannada", duration_mins=156, rating=4.7, poster_url=DEFAULT_POSTER, tags="mass"),
        Movie(title="KGF Chapter 2", description="Rocky fights to keep his empire.", genre="Action", language="Kannada", duration_mins=168, rating=4.8, poster_url=DEFAULT_POSTER, tags="mass"),
        Movie(title="2018", description="Survivors battle a historic flood in Kerala.", genre="Drama", language="Malayalam", duration_mins=150, rating=4.6, poster_url=DEFAULT_POSTER, tags="real"),
        Movie(title="Drishyam", description="A family fights to protect a dark secret.", genre="Thriller", language="Malayalam", duration_mins=160, rating=4.8, poster_url=DEFAULT_POSTER, tags="crime"),
        Movie(title="Oppenheimer", description="The story of the father of the atomic bomb.", genre="Drama", language="English", duration_mins=180, rating=4.7, poster_url=DEFAULT_POSTER, tags="biopic"),
        Movie(title="Avengers: Endgame", description="The Avengers unite for a final stand.", genre="Action", language="English", duration_mins=181, rating=4.9, poster_url=DEFAULT_POSTER, tags="marvel"),
        Movie(title="Interstellar", description="A mission across space to save humanity.", genre="Sci-Fi", language="English", duration_mins=169, rating=4.8, poster_url=DEFAULT_POSTER, tags="space"),
    ]

    theatres = [
        Theatre(name="PVR Orion Mall", city="Bengaluru", address="Rajajinagar"),
        Theatre(name="INOX Garuda Mall", city="Bengaluru", address="MG Road"),
        Theatre(name="Cinepolis Forum Mall", city="Bengaluru", address="Koramangala"),
        Theatre(name="AMB Cinemas", city="Hyderabad", address="Gachibowli"),
        Theatre(name="Prasads Multiplex", city="Hyderabad", address="NTR Marg"),
        Theatre(name="PVR Next Galleria", city="Hyderabad", address="Panjagutta"),
        Theatre(name="Sathyam Cinemas", city="Chennai", address="Royapettah"),
        Theatre(name="PVR VR Mall", city="Chennai", address="Anna Nagar"),
        Theatre(name="INOX Marina Mall", city="Chennai", address="OMR"),
        Theatre(name="PVR Phoenix Mall", city="Mumbai", address="Lower Parel"),
        Theatre(name="INOX Nariman Point", city="Mumbai", address="Nariman Point"),
        Theatre(name="Cinepolis Andheri", city="Mumbai", address="Andheri"),
        Theatre(name="PVR Ripples Mall", city="Vijayawada", address="MG Road"),
        Theatre(name="INOX LEPL Icon", city="Vijayawada", address="Patamata"),
    ]

    movie_map: dict[str, Movie] = {}
    for movie in movies:
        existing_movie = _get_movie_by_title(session, movie.title)
        if existing_movie:
            existing_movie.description = movie.description
            existing_movie.genre = movie.genre
            existing_movie.language = movie.language
            existing_movie.duration_mins = movie.duration_mins
            existing_movie.rating = movie.rating
            if not existing_movie.poster_url:
                existing_movie.poster_url = movie.poster_url
            existing_movie.tags = movie.tags
            movie_map[movie.title] = existing_movie
        else:
            session.add(movie)
            session.flush()
            movie_map[movie.title] = movie

    theatre_map: dict[tuple[str, str], Theatre] = {}
    for theatre in theatres:
        existing_theatre = _get_theatre_by_name_city(session, theatre.name, theatre.city)
        if existing_theatre:
            existing_theatre.address = theatre.address
            theatre_map[(theatre.name, theatre.city)] = existing_theatre
        else:
            session.add(theatre)
            session.flush()
            theatre_map[(theatre.name, theatre.city)] = theatre

    session.commit()

    screens = []
    for theatre in theatre_map.values():
        existing = session.exec(select(Screen).where(Screen.theatre_id == theatre.id)).all()
        if existing:
            screens.extend(existing)
            continue
        screens.append(Screen(theatre_id=theatre.id, name="Screen 1", seat_map=build_seat_map(), capacity=160))
        screens.append(Screen(theatre_id=theatre.id, name="Screen 2", seat_map=build_seat_map(12, 18), capacity=216))
        screens.append(Screen(theatre_id=theatre.id, name="IMAX", seat_map=build_seat_map(14, 20), capacity=280))
    session.add_all(screens)
    session.commit()

    now = datetime.utcnow()
    showtimes = []
    formats = ["2D", "3D", "IMAX"]
    for movie in movie_map.values():
        existing_show = session.exec(select(Showtime).where(Showtime.movie_id == movie.id)).first()
        if existing_show:
            continue
        for screen in screens:
            for _ in range(3):
                showtimes.append(
                    Showtime(
                        movie_id=movie.id,
                        screen_id=screen.id,
                        start_time=now + timedelta(hours=random.randint(1, 72)),
                        base_price=random.choice([150, 200, 250, 300, 400, 500]),
                        format=random.choice(formats),
                    )
                )
    session.add_all(showtimes)
    session.commit()
