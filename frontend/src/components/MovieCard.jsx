import React from 'react'

const MovieCard = ({ movie, compact, onSelect }) => {
  return (
    <div className={`movie-card ${compact ? 'compact' : ''}`}>
      <img src={movie.poster_url} alt={movie.title} />
      <div className="movie-info">
        <h3>{movie.title}</h3>
        <p>{movie.description}</p>
        <div className="meta">
          <span>{movie.genre}</span>
          <span>{movie.language}</span>
          <span>{movie.duration_mins} mins</span>
          <span className="rating">{movie.rating.toFixed(1)}</span>
        </div>
        {!compact && onSelect && (
          <button className="ghost small" onClick={() => onSelect(movie)}>
            View Showtimes
          </button>
        )}
      </div>
    </div>
  )
}

export default MovieCard
