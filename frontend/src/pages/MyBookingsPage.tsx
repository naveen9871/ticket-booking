import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import api from '../api'
import { useAuth } from '../hooks/useAuth'

interface BookingItem {
  id: number
  showtime_id: number
  seats: string[]
  total_price: number
  status: string
  created_at: string
  movie_title: string | null
  movie_poster: string | null
  theatre_name: string | null
  theatre_city: string | null
  screen_name: string | null
  showtime_format: string | null
  start_time: string | null
}

const STATUS_COLORS: Record<string, string> = {
  CONFIRMED: '#22C55E',
  CANCELLED: '#EF4444',
  PENDING: '#F5A623',
}

const STATUS_BG: Record<string, string> = {
  CONFIRMED: 'rgba(34,197,94,0.12)',
  CANCELLED: 'rgba(239,68,68,0.12)',
  PENDING: 'rgba(245,166,35,0.12)',
}

export default function MyBookingsPage() {
  const navigate = useNavigate()
  const { isLoggedIn } = useAuth()
  const [bookings, setBookings] = useState<BookingItem[]>([])
  const [loading, setLoading] = useState(true)
  const [cancellingId, setCancellingId] = useState<number | null>(null)
  const [filter, setFilter] = useState<'ALL' | 'CONFIRMED' | 'CANCELLED'>('ALL')

  useEffect(() => {
    if (!isLoggedIn) { navigate('/login'); return }
    api.get('/bookings').then(r => setBookings(r.data)).catch(() => setBookings([])).finally(() => setLoading(false))
  }, [isLoggedIn, navigate])

  const cancelBooking = async (id: number) => {
    if (!confirm('Cancel this booking? A refund will be processed as per policy.')) return
    setCancellingId(id)
    try {
      await api.post(`/bookings/${id}/cancel`)
      setBookings(prev => prev.map(b => b.id === id ? { ...b, status: 'CANCELLED' } : b))
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Cancellation failed.')
    } finally {
      setCancellingId(null)
    }
  }

  const filtered = bookings.filter(b => filter === 'ALL' || b.status === filter)

  const upcoming = filtered.filter(b => b.start_time && new Date(b.start_time) > new Date() && b.status === 'CONFIRMED')
  const past = filtered.filter(b => !upcoming.includes(b))

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'var(--surface-base)' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ width: 40, height: 40, border: '3px solid rgba(245,166,35,0.3)', borderTopColor: '#F5A623', borderRadius: '50%', animation: 'spin-slow 1s linear infinite', margin: '0 auto 12px' }} />
        <p style={{ color: 'var(--text-muted)' }}>Loading your bookings…</p>
      </div>
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface-base)', padding: '32px 16px' }}>
      <div style={{ maxWidth: 720, margin: '0 auto' }}>

        <button className="btn btn-ghost btn-sm" style={{ marginBottom: 20 }} onClick={() => navigate('/')}>← Back</button>

        <p className="eyebrow">Account</p>
        <h1 style={{ fontSize: 32, fontWeight: 800, fontFamily: "'Space Grotesk',sans-serif", marginBottom: 8, marginTop: 4 }}>
          My Bookings
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 28 }}>
          {bookings.length} booking{bookings.length !== 1 ? 's' : ''} total
        </p>

        {/* Filter tabs */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 28 }}>
          {(['ALL', 'CONFIRMED', 'CANCELLED'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '7px 16px',
                borderRadius: 99,
                border: `1px solid ${filter === f ? 'rgba(245,166,35,0.5)' : 'rgba(255,255,255,0.1)'}`,
                background: filter === f ? 'rgba(245,166,35,0.12)' : 'transparent',
                color: filter === f ? '#F5A623' : 'rgba(237,244,242,0.6)',
                fontSize: 13,
                fontWeight: filter === f ? 600 : 400,
                cursor: 'pointer',
              }}
            >
              {f === 'ALL' ? `All (${bookings.length})` : f === 'CONFIRMED' ? `Active (${bookings.filter(b => b.status === 'CONFIRMED').length})` : `Cancelled (${bookings.filter(b => b.status === 'CANCELLED').length})`}
            </button>
          ))}
        </div>

        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🎟️</div>
            <p style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-secondary)' }}>No bookings yet</p>
            <p style={{ fontSize: 14, marginTop: 8 }}>Book your first movie ticket to see it here.</p>
            <button className="btn btn-primary" style={{ marginTop: 24 }} onClick={() => navigate('/')}>Browse Movies</button>
          </div>
        )}

        {upcoming.length > 0 && (
          <div style={{ marginBottom: 32 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: '#22C55E', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>🎬</span> Upcoming Shows
            </h2>
            <AnimatePresence>
              {upcoming.map(b => <BookingCard key={b.id} booking={b} onCancel={cancelBooking} cancellingId={cancellingId} navigate={navigate} />)}
            </AnimatePresence>
          </div>
        )}

        {past.length > 0 && (
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>📅</span> Past & Cancelled
            </h2>
            <AnimatePresence>
              {past.map(b => <BookingCard key={b.id} booking={b} onCancel={cancelBooking} cancellingId={cancellingId} navigate={navigate} />)}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  )
}

function BookingCard({ booking: b, onCancel, cancellingId, navigate }: {
  booking: BookingItem
  onCancel: (id: number) => void
  cancellingId: number | null
  navigate: (path: string) => void
}) {
  const isPast = b.start_time ? new Date(b.start_time) < new Date() : false
  const canCancel = b.status === 'CONFIRMED' && !isPast

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      style={{
        background: 'var(--surface-02)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 14,
        overflow: 'hidden',
        marginBottom: 16,
        opacity: b.status === 'CANCELLED' ? 0.65 : 1,
      }}
    >
      <div style={{ display: 'flex', gap: 0 }}>
        {/* Poster */}
        <div style={{
          width: 80,
          flexShrink: 0,
          background: b.movie_poster
            ? `url(${b.movie_poster}) center/cover`
            : 'linear-gradient(135deg, #F5A623, #EF4444)',
          minHeight: 110,
        }} />

        {/* Details */}
        <div style={{ flex: 1, padding: '14px 16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, marginBottom: 6 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 15, color: '#EDF4F2', fontFamily: "'Space Grotesk',sans-serif" }}>
                {b.movie_title || `Booking #${b.id}`}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                {b.theatre_name} · {b.theatre_city}
              </div>
            </div>
            <span style={{
              fontSize: 11,
              fontWeight: 600,
              padding: '3px 10px',
              borderRadius: 99,
              background: STATUS_BG[b.status] || 'rgba(255,255,255,0.08)',
              color: STATUS_COLORS[b.status] || '#EDF4F2',
              flexShrink: 0,
            }}>{b.status}</span>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 16px', fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12 }}>
            {b.start_time && (
              <span>📅 {new Date(b.start_time).toLocaleString([], { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</span>
            )}
            <span>🪑 {(b.seats || []).join(', ')}</span>
            {b.showtime_format && <span>🎞️ {b.showtime_format}</span>}
            <span>💰 ₹{b.total_price}</span>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            {b.status === 'CONFIRMED' && (
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => navigate(`/ticket/${b.id}`)}
              >
                🎟️ View Ticket
              </button>
            )}
            {canCancel && (
              <button
                className="btn btn-sm"
                style={{ background: 'rgba(239,68,68,0.1)', color: '#EF4444', border: '1px solid rgba(239,68,68,0.3)' }}
                onClick={() => onCancel(b.id)}
                disabled={cancellingId === b.id}
              >
                {cancellingId === b.id ? 'Cancelling…' : '✕ Cancel'}
              </button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
