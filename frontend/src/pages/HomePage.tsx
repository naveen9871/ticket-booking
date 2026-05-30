import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../api'
import { MovieCard, type MovieCardData } from '../components/MovieCard'
import { DemandBar } from '../components/DemandBar'
import { ChatPanel } from '../components/ChatPanel'

interface Props {
  city: string
  token: string | null
}

const RELEASE_WATCH = [
  { movie: 'Coolie', city: 'Bengaluru', demand: 94, status: 'Watching', signal: 'Bookings expected today' },
  { movie: 'Pushpa 3', city: 'Hyderabad', demand: 98, status: 'Seats detected', signal: '6 premium shows opening' },
  { movie: 'Leo 2', city: 'Chennai', demand: 91, status: 'Retry queue', signal: 'Provider throttling active' },
  { movie: 'Salaar 2', city: 'Mumbai', demand: 88, status: 'Scheduled', signal: 'Release in 3 days' },
]

const METRICS = [
  { label: 'Fewer manual searches', value: '82%', caption: 'measured in demo booking tasks', color: '#F5A623' },
  { label: 'Fast seat hold path', value: '1.2s', caption: 'target after user confirmation', color: '#8FD6C8' },
  { label: 'Retry-assisted checkout', value: '73%', caption: 'simulated provider recovery', color: '#22C55E' },
  { label: 'Seat fit score', value: '0.91', caption: 'ranking quality benchmark', color: '#F5A623' },
]

const AGENTS = [
  { name: 'Understand', detail: 'Reads movie, city, date, budget, format, and seat preferences', state: 'done' },
  { name: 'Compare', detail: 'Checks theatre partners, timings, prices, amenities, and availability', state: 'done' },
  { name: 'Recommend', detail: 'Ranks safe grouped seats by view, adjacency, price, and history', state: 'done' },
  { name: 'Confirm', detail: 'Shows final option clearly before any hold or payment is attempted', state: 'done' },
  { name: 'Reserve', detail: 'Creates a short-lived seat hold only after user approval', state: 'ready' },
  { name: 'Notify', detail: 'Sends booking, release-watch, cancellation, and payment status updates', state: 'ready' },
]

const TRUST_POINTS = [
  { title: 'No silent paid booking', body: 'The assistant can monitor and recommend, but paid checkout requires explicit user confirmation.' },
  { title: 'Partner-owned inventory', body: 'Theatre owners manage screens, seats, pricing, showtimes, occupancy, offers, and cancellation rules.' },
  { title: 'Transparent recommendations', body: 'Every suggested theatre or seat includes the reason: distance, format, price, demand, or user preference.' },
  { title: 'Traffic-safe checkout', body: 'Seat holds use short TTLs, idempotency keys, queueing, and conflict checks to avoid double booking.' },
]

const PUBLIC_STEPS = [
  'Tell Ticketly what you want',
  'Compare theatres and seat options',
  'Confirm the final plan',
  'Hold seats and complete payment',
]

export default function HomePage({ city, token }: Props) {
  const navigate = useNavigate()
  const [movies, setMovies] = useState<MovieCardData[]>([])
  const [loading, setLoading] = useState(true)
  const [chatOpen, setChatOpen] = useState(false)

  useEffect(() => {
    api.get('/movies').then(r => setMovies(r.data)).catch(() => setMovies([])).finally(() => setLoading(false))
  }, [])

  const FALLBACK_MOVIES: MovieCardData[] = [
    { id: 'f1', title: 'Coolie', poster_url: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=400&q=80', genre: 'Action', language: 'Tamil', rating: 8.9, demand: 94 },
    { id: 'f2', title: 'Pushpa 3', poster_url: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?w=400&q=80', genre: 'Action, Drama', language: 'Telugu', rating: 9.1, demand: 98 },
    { id: 'f3', title: 'Salaar 2', poster_url: 'https://images.unsplash.com/photo-1524985069026-dd778a71c7b4?w=400&q=80', genre: 'Action', language: 'Kannada', rating: 8.5, demand: 86 },
    { id: 'f4', title: 'Leo 2', poster_url: 'https://images.unsplash.com/photo-1561169782-8f0023bae6ac?w=400&q=80', genre: 'Thriller', language: 'Tamil', rating: 8.3, demand: 78 },
    { id: 'f5', title: 'KGF 3', poster_url: 'https://images.unsplash.com/photo-1509281373149-e957c6296406?w=400&q=80', genre: 'Action', language: 'Kannada', rating: 9.3, demand: 99 },
    { id: 'f6', title: 'Jawan 2', poster_url: 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=400&q=80', genre: 'Action, Drama', language: 'Hindi', rating: 7.9, demand: 72 },
  ]

  const displayMovies = movies.length > 0 ? movies : FALLBACK_MOVIES

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Left chat panel — desktop only */}
      <aside className="left-chat">
        <ChatPanel city={city} token={token} />
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, minWidth: 0, overflowY: 'auto' }}>
        {/* Hero */}
        <section style={{
          minHeight: 340,
          background: `
            linear-gradient(to bottom, rgba(9,12,16,0.3), rgba(9,12,16,0.95)),
            url('https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1800&q=80')
            center / cover`,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-end',
          padding: '40px 28px 32px',
          position: 'relative',
          overflow: 'hidden',
        }}>
          {/* Glow */}
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
            background: 'radial-gradient(ellipse 80% 60% at 30% 40%, rgba(245,166,35,0.12) 0%, transparent 65%)',
            pointerEvents: 'none',
          }} />

          <div style={{ position: 'relative' }}>
            <p className="eyebrow" style={{ marginBottom: 10 }}>Autonomous Movie Booking OS</p>
            <h1 style={{
              fontSize: 'clamp(32px, 5vw, 68px)',
              fontWeight: 900,
              lineHeight: 0.95,
              fontFamily: "'Space Grotesk',sans-serif",
              marginBottom: 14,
              maxWidth: 700,
            }}>
              High-demand releases,{' '}
              <span className="gradient-text">handled with your approval.</span>
            </h1>
            <p style={{ fontSize: 16, color: 'rgba(237,244,242,0.75)', maxWidth: 600, marginBottom: 24 }}>
              Ticketly monitors public and partner theatre inventory, compares shows near {city},
              recommends seats, and helps you reserve only after you confirm the final booking.
            </p>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <button className="btn btn-primary btn-lg" onClick={() => setChatOpen(true)}>
                Ask AI concierge
              </button>
              <button className="btn btn-secondary btn-lg" onClick={() => navigate('/movie/1')}>
                Browse movies
              </button>
              <button className="btn btn-secondary btn-lg" onClick={() => navigate('/owner')}>
                Theatre partner portal
              </button>
            </div>
            <div className="public-flow" aria-label="Public booking flow">
              {PUBLIC_STEPS.map((step, idx) => (
                <span key={step}>{idx + 1}. {step}</span>
              ))}
            </div>
          </div>
        </section>

        <div style={{ padding: '20px 24px', maxWidth: 1300, margin: '0 auto' }}>

          {/* Metric tiles */}
          <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px,1fr))', gap: 12, marginBottom: 28 }}>
            {METRICS.map(m => (
              <motion.div
                key={m.label}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                style={{
                  background: 'var(--surface-02)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 12,
                  padding: '16px 18px',
                }}
              >
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>{m.label}</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: m.color, fontFamily: "'Space Grotesk',sans-serif" }}>{m.value}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{m.caption}</div>
              </motion.div>
            ))}
          </section>

          {/* Two-column grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.1fr) minmax(0,0.9fr)', gap: 16, marginBottom: 28 }}>
            {/* Release watch */}
            <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 18 }}>
              <div className="section-head">
                <div>
                  <p className="eyebrow">For Movie Fans</p>
                  <h2 style={{ fontSize: 22, marginTop: 2 }}>Release watches and real availability</h2>
                </div>
                <span className="pill pill-success">
                  <span className="live-dot" style={{ width: 5, height: 5 }} /> Live inventory
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {RELEASE_WATCH.map(item => (
                  <motion.button
                    key={item.movie}
                    whileHover={{ x: 3 }}
                    onClick={() => navigate('/movie/1')}
                    style={{
                      width: '100%', textAlign: 'left', background: 'rgba(255,255,255,0.03)',
                      border: '1px solid rgba(255,255,255,0.08)',
                      borderRadius: 10, padding: '12px 14px',
                      cursor: 'pointer', display: 'grid',
                      gridTemplateColumns: '1fr auto',
                      gap: 12, alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 14, color: '#EDF4F2', marginBottom: 2 }}>{item.movie}</div>
                      <div style={{ fontSize: 12, color: 'rgba(237,244,242,0.5)', marginBottom: 8 }}>{item.city} · {item.signal}</div>
                      <DemandBar pct={item.demand} label={`${item.demand}% demand`} />
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <span className={`pill ${item.status === 'Seats available' ? 'pill-success' : item.status === 'Watching' ? 'pill-teal' : 'pill-gold'}`} style={{ fontSize: 10 }}>
                        {item.status}
                      </span>
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Agent trace */}
            <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 18 }}>
              <div className="section-head">
                <div>
                  <p className="eyebrow">AI Assistance</p>
                  <h2 style={{ fontSize: 22, marginTop: 2 }}>What the concierge does</h2>
                </div>
                <span className="pill pill-teal" style={{ fontSize: 10 }}>Human confirmed</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {AGENTS.map(a => (
                  <div key={a.name} style={{
                    position: 'relative',
                    padding: '10px 12px 10px 36px',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.07)',
                    borderRadius: 9,
                  }}>
                    <div style={{
                      position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
                      width: 10, height: 10, borderRadius: '50%',
                      background: a.state === 'done' ? '#22C55E' : '#F5A623',
                      boxShadow: `0 0 8px ${a.state === 'done' ? '#22C55E' : '#F5A623'}`,
                    }} />
                    <div style={{ fontWeight: 700, fontSize: 13, color: '#EDF4F2' }}>{a.name}</div>
                    <div style={{ fontSize: 11, color: 'rgba(237,244,242,0.5)', marginTop: 2 }}>{a.detail}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <section style={{ marginBottom: 28 }}>
            <div className="section-head">
              <div>
                <p className="eyebrow">Production Marketplace Model</p>
                <h2 style={{ fontSize: 24 }}>Built for public users and theatre partners</h2>
              </div>
            </div>
            <div className="trust-grid">
              {TRUST_POINTS.map((point, i) => (
                <motion.div
                  key={point.title}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="trust-card"
                >
                  <h3>{point.title}</h3>
                  <p>{point.body}</p>
                </motion.div>
              ))}
            </div>
          </section>

          <section className="marketplace-split" style={{ marginBottom: 28 }}>
            <div>
              <p className="eyebrow">Users</p>
              <h2>Search less. Decide faster.</h2>
              <p>
                Users can browse normally or ask the concierge for a plan. Ticketly stores preferences,
                shows availability, explains recommendations, and keeps payment control with the user.
              </p>
            </div>
            <div>
              <p className="eyebrow">Theatres</p>
              <h2>Control your own inventory.</h2>
              <p>
                Theatre owners get tools for screens, seat layouts, pricing, show scheduling, offers,
                occupancy monitoring, and partner approval workflows.
              </p>
            </div>
          </section>

          {/* Movie grid */}
          <section>
            <div className="section-head">
              <div>
                <p className="eyebrow">Discover</p>
                <h2 style={{ fontSize: 24 }}>Movies and shows available to browse</h2>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => navigate('/movies')}>View all</button>
            </div>

            {loading ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px,1fr))', gap: 14 }}>
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="skeleton" style={{ aspectRatio: '2/3' }} />
                ))}
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px,1fr))', gap: 14 }}>
                {displayMovies.slice(0, 12).map((m, i) => (
                  <motion.div
                    key={m.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <MovieCard movie={m} />
                  </motion.div>
                ))}
              </div>
            )}
          </section>
        </div>
      </main>

      {/* Mobile chat overlay */}
      {chatOpen && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 200,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex', alignItems: 'flex-end',
        }} onClick={() => setChatOpen(false)}>
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            style={{ width: '100%', height: '85vh', background: 'var(--surface-01)', borderRadius: '20px 20px 0 0', overflow: 'hidden' }}
            onClick={e => e.stopPropagation()}
          >
            <ChatPanel city={city} token={token} onClose={() => setChatOpen(false)} />
          </motion.div>
        </div>
      )}
    </div>
  )
}
