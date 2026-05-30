import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../api'
import { TheatreCard } from '../components/TheatreCard'
import { DemandBar } from '../components/DemandBar'

const FORMATS = ['All', 'IMAX', 'Dolby', '4DX', '2D', '3D']

interface Showtime {
  id: number
  movie_id: number
  start_time: string
  base_price: number
  format: string
  status: string
  movie_title?: string
  theatre_name?: string
  theatre_id?: number
  screen_name?: string
  city?: string
}

const FALLBACK_MOVIE = {
  id: 1, title: 'Coolie', description: 'An electrifying action blockbuster from director Lokesh Kanagaraj starring Rajinikanth as a fiery railway coolie turned vigilante. A mass entertainer with top-notch action sequences and a gripping storyline.',
  genre: 'Action, Thriller', language: 'Tamil', duration_mins: 172, rating: 9.1,
  poster_url: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=600&q=80',
  tags: 'Mass, Action, Rajini',
}

export default function MovieDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [movie, setMovie] = useState<typeof FALLBACK_MOVIE | null>(null)
  const [showtimes, setShowtimes] = useState<Showtime[]>([])
  const [selectedFormat, setSelectedFormat] = useState('All')
  const [selectedDate, setSelectedDate] = useState(0)
  const [loading, setLoading] = useState(true)

  const dates = Array.from({ length: 5 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() + i)
    return d
  })

  useEffect(() => {
    Promise.allSettled([
      api.get(`/movies/${id}`),
      api.get(`/showtimes/?movie_id=${id}&limit=30`),
    ]).then(([movieRes, stRes]) => {
      if (movieRes.status === 'fulfilled') setMovie(movieRes.value.data)
      else setMovie(FALLBACK_MOVIE)
      if (stRes.status === 'fulfilled') setShowtimes(stRes.value.data)
    }).finally(() => setLoading(false))
  }, [id])

  const filteredShowtimes = showtimes.filter(st => {
    const d = new Date(st.start_time)
    const target = dates[selectedDate]
    const sameDay = d.getDate() === target.getDate() && d.getMonth() === target.getMonth()
    const sameFormat = selectedFormat === 'All' || st.format?.toLowerCase().includes(selectedFormat.toLowerCase())
    return sameDay && sameFormat
  })

  const fallbackShowtimes: Showtime[] = Array.from({ length: 8 }, (_, i) => ({
    id: i + 1,
    movie_id: Number(id) || 1,
    start_time: new Date(Date.now() + (i * 3 + 6) * 3600000).toISOString(),
    base_price: [240, 320, 480, 560, 680][i % 5],
    format: ['2D', 'IMAX', 'Dolby Atmos', '4DX', '3D'][i % 5],
    status: 'SCHEDULED',
    theatre_name: ['PVR Orion', 'INOX Vega', 'PVR Forum', 'Cinepolis Nexus', 'Miraj Cinemas'][i % 5],
    screen_name: `Screen ${(i % 4) + 1}`,
    city: 'Bengaluru',
  }))

  const displayShowtimes = filteredShowtimes.length > 0 ? filteredShowtimes : fallbackShowtimes
  const m = movie || FALLBACK_MOVIE

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface-base)' }}>
      {/* Hero banner */}
      <div style={{
        position: 'relative', height: 420, overflow: 'hidden',
        background: `linear-gradient(to bottom, rgba(9,12,16,0.1) 0%, rgba(9,12,16,0.97) 100%), url('${m.poster_url}') center/cover`,
      }}>
        <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: '0 32px 36px' }}>
          <div style={{ display: 'flex', gap: 24, alignItems: 'flex-end', maxWidth: 1200 }}>
            <img
              src={m.poster_url}
              alt={m.title}
              style={{ width: 140, borderRadius: 12, border: '2px solid rgba(255,255,255,0.15)', boxShadow: '0 8px 32px rgba(0,0,0,0.6)', flexShrink: 0 }}
              onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
            />
            <div>
              <p className="eyebrow" style={{ marginBottom: 8 }}>{m.genre} · {m.language} · {m.duration_mins} min</p>
              <h1 style={{ fontSize: 'clamp(28px,4vw,56px)', fontWeight: 900, fontFamily: "'Space Grotesk',sans-serif", marginBottom: 10, lineHeight: 1 }}>
                {m.title}
              </h1>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 14 }}>
                <span style={{ fontSize: 18, fontWeight: 700, color: '#F5A623' }}>⭐ {m.rating}</span>
                {m.tags?.split(',').slice(0, 3).map(t => (
                  <span key={t} className="pill pill-teal" style={{ fontSize: 10 }}>{t.trim()}</span>
                ))}
              </div>
              <p style={{ color: 'rgba(237,244,242,0.65)', fontSize: 14, maxWidth: 600, lineHeight: 1.6 }}>{m.description}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 320px', gap: 24 }}>
          {/* Left — showtime picker */}
          <div>
            {/* Date tabs */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
              {dates.map((d, i) => (
                <button
                  key={i}
                  onClick={() => setSelectedDate(i)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: 9,
                    background: selectedDate === i ? 'rgba(245,166,35,0.15)' : 'rgba(255,255,255,0.04)',
                    border: `1px solid ${selectedDate === i ? 'rgba(245,166,35,0.5)' : 'rgba(255,255,255,0.1)'}`,
                    color: selectedDate === i ? '#F5A623' : 'rgba(237,244,242,0.7)',
                    fontSize: 13, fontWeight: 600,
                    cursor: 'pointer', transition: 'all 0.15s',
                    flexShrink: 0,
                  }}
                >
                  <div>{d.toLocaleDateString('en', { weekday: 'short' })}</div>
                  <div style={{ fontSize: 11, fontWeight: 400, opacity: 0.7 }}>{d.getDate()} {d.toLocaleDateString('en', { month: 'short' })}</div>
                </button>
              ))}
            </div>

            {/* Format filter */}
            <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
              {FORMATS.map(f => (
                <button
                  key={f}
                  onClick={() => setSelectedFormat(f)}
                  className={`pill ${selectedFormat === f ? 'pill-gold' : ''}`}
                  style={{
                    cursor: 'pointer', border: '1px solid',
                    background: selectedFormat === f ? 'rgba(245,166,35,0.15)' : 'rgba(255,255,255,0.04)',
                    borderColor: selectedFormat === f ? 'rgba(245,166,35,0.5)' : 'rgba(255,255,255,0.1)',
                    color: selectedFormat === f ? '#F5A623' : 'rgba(237,244,242,0.6)',
                    padding: '5px 12px', borderRadius: 999, fontSize: 12, fontWeight: 600,
                    transition: 'all 0.15s',
                  }}
                >{f}</button>
              ))}
            </div>

            {/* Showtimes */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {displayShowtimes.map((st, i) => (
                <motion.div
                  key={st.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  style={{
                    display: 'grid', gridTemplateColumns: '90px 1fr auto auto',
                    gap: 14, alignItems: 'center',
                    background: 'var(--surface-02)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 12, padding: '14px 16px',
                  }}
                >
                  <div>
                    <div style={{ fontSize: 20, fontWeight: 800, fontFamily: "'Space Grotesk',sans-serif", color: '#EDF4F2' }}>
                      {new Date(st.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                      {new Date(st.start_time).toLocaleDateString('en', { weekday: 'short', day: 'numeric', month: 'short' })}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 3 }}>{st.theatre_name || 'Theatre'}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{st.screen_name} · {st.city}</div>
                    <span className="pill pill-teal" style={{ fontSize: 9, marginTop: 6, display: 'inline-block' }}>{st.format}</span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 18, fontWeight: 800, color: '#F5A623' }}>₹{st.base_price}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>per seat</div>
                  </div>
                  <button
                    className="btn btn-primary"
                    onClick={() => navigate(`/seats/${st.id}`)}
                    style={{ padding: '10px 16px' }}
                  >
                    Book →
                  </button>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Right — theatre info */}
          <div>
            <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 18, marginBottom: 16 }}>
              <p className="eyebrow" style={{ marginBottom: 10 }}>AI Demand Forecast</p>
              <DemandBar pct={94} label="Overall demand" color="gold" />
              <div style={{ marginTop: 10 }}>
                <DemandBar pct={78} label="Weekend availability" color="teal" />
              </div>
              <div style={{ marginTop: 10 }}>
                <DemandBar pct={56} label="IMAX seats remaining" color="teal" />
              </div>
              <div className="notif-bar" style={{ marginTop: 14 }}>
                <span>🔔</span>
                <span style={{ fontSize: 12 }}>Set a booking alert for this movie</span>
                <button className="btn btn-primary btn-sm" style={{ marginLeft: 'auto', flexShrink: 0 }}>Alert me</button>
              </div>
            </div>

            <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 18 }}>
              <p className="eyebrow" style={{ marginBottom: 12 }}>Top Theatres Nearby</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  { id: 1, name: 'PVR Orion IMAX', city: 'Bengaluru', address: 'Rajajinagar', supported_formats: ['IMAX', 'Dolby'], base_price: 560, score: 96, rank: 1 },
                  { id: 2, name: 'INOX Vega City', city: 'Bengaluru', address: 'Bannerghatta Rd', supported_formats: ['4DX', '3D'], base_price: 420, score: 91, rank: 2 },
                  { id: 3, name: 'Cinepolis Nexus', city: 'Bengaluru', address: 'Whitefield', supported_formats: ['2D', 'Dolby'], base_price: 320, score: 86, rank: 3 },
                ].map(t => (
                  <TheatreCard key={t.id} theatre={t} onClick={() => {}} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
