import { useNavigate } from 'react-router-dom'
import { DemandBar } from './DemandBar'

export interface MovieCardData {
  id: number | string
  title: string
  poster_url: string
  genre: string
  language: string
  rating: number
  duration_mins?: number
  tags?: string
  demand?: number
}

interface Props {
  movie: MovieCardData
  compact?: boolean
}

export function MovieCard({ movie, compact = false }: Props) {
  const navigate = useNavigate()
  const demand = movie.demand ?? Math.floor(60 + Math.random() * 38)

  return (
    <div
      className="movie-poster-card"
      onClick={() => navigate(`/movie/${movie.id}`)}
      style={compact ? { aspectRatio: '3/4' } : undefined}
    >
      <img
        src={movie.poster_url}
        alt={movie.title}
        loading="lazy"
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        onError={(e) => {
          const t = e.target as HTMLImageElement
          t.src = `https://placehold.co/300x450/141C28/8FD6C8?text=${encodeURIComponent(movie.title.slice(0, 10))}`
        }}
      />

      {/* Gradient overlay */}
      <div className="movie-poster-overlay">
        {/* Rating badge */}
        <div style={{
          position: 'absolute', top: 10, right: 10,
          background: 'rgba(0,0,0,0.75)',
          border: '1px solid rgba(245,166,35,0.4)',
          borderRadius: 6,
          padding: '2px 7px',
          fontSize: 12,
          fontWeight: 700,
          color: '#F5A623',
        }}>⭐ {movie.rating.toFixed(1)}</div>

        {/* Genre pill */}
        <div style={{ marginBottom: 6 }}>
          <span className="pill pill-teal" style={{ fontSize: 10 }}>{movie.genre.split(',')[0].trim()}</span>
          <span style={{ marginLeft: 6, fontSize: 10, color: 'rgba(237,244,242,0.5)' }}>{movie.language}</span>
        </div>

        <h3 style={{ fontSize: compact ? 13 : 15, fontWeight: 700, lineHeight: 1.2, marginBottom: 6, color: '#EDF4F2' }}>
          {movie.title}
        </h3>

        <DemandBar pct={demand} />
      </div>
    </div>
  )
}
