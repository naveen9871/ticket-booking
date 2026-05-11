import React from 'react'

const MovieCard = ({ movie, compact = false, onSelect }) => {
  return (
    <article className={`movie-card ${compact ? 'compact' : ''}`}>
      <div className="movie-poster-wrap">
        <img className="movie-poster" src={movie.poster_url} alt={movie.title} />
        <div className="movie-overlay">
          <span className="pill">{movie.language}</span>
          <span className="rating-badge">{movie.rating.toFixed(1)}</span>
        </div>
      </div>

      <div className="movie-info">
        <div className="movie-title-row">
          <h3>{movie.title}</h3>
          <span className="movie-duration">{movie.duration_mins}m</span>
        </div>
        <p>{movie.description}</p>
        <div className="meta">
          <span>{movie.genre}</span>
          <span>{movie.language}</span>
          <span>Priority Seats</span>
        </div>
        {onSelect && (
          <button className="ghost small" onClick={() => onSelect(movie)}>
            {compact ? 'Open Showtimes' : 'See Experience'}
          </button>
        )}
      </div>
    </article>
  )
}

export default MovieCard
