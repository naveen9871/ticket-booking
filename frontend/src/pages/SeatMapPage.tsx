import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../api'
import { SeatMap, type SeatData } from '../components/SeatMap'

const WS_BASE = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8001'

const SESSION_KEY = typeof window !== 'undefined' && window.crypto?.randomUUID
  ? window.crypto.randomUUID()
  : Math.random().toString(36).slice(2)

function buildFallbackSeats(): SeatData[] {
  const rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
  const seats: SeatData[] = []
  rows.forEach((row, ri) => {
    for (let n = 1; n <= 14; n++) {
      const roll = Math.random()
      const status: SeatData['status'] = roll > 0.78 ? 'booked' : roll > 0.72 ? 'held' : 'available'
      const type: SeatData['type'] = ri >= 7 ? 'recliner' : n <= 2 || n >= 13 ? 'wheelchair' : 'standard'
      const isAiPick = status === 'available' && ri === 4 && n >= 5 && n <= 9
      seats.push({ id: `${row}${n}`, row, number: n, type, status, price: type === 'recliner' ? 620 : 360, isAiPick })
    }
  })
  return seats
}

export default function SeatMapPage() {
  const { showtimeId } = useParams<{ showtimeId: string }>()
  const navigate = useNavigate()
  const [seats, setSeats] = useState<SeatData[]>([])
  const [selectedSeats, setSelectedSeats] = useState<string[]>([])
  const [showtime, setShowtime] = useState<Record<string, unknown> | null>(null)
  const [holdInfo, setHoldInfo] = useState<{ hold_token: string; expires_at: string } | null>(null)
  const [pricing, setPricing] = useState<{ total: number } | null>(null)
  const [loadingHold, setLoadingHold] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [liveUpdate, setLiveUpdate] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    api.get(`/showtimes/${showtimeId}/seats`, {
      params: { count: 2, session_key: SESSION_KEY },
    }).then(r => {
      const raw = r.data.seat_map as any[][]
      const flat: SeatData[] = raw.flat().map(s => ({
        id: s.id,
        row: s.id[0],
        number: parseInt(s.id.slice(1)),
        type: 'standard',
        status: s.status === 'BOOKED' ? 'booked' : s.status === 'HELD' ? 'held' : 'available',
        price: s.price ?? 360,
        isAiPick: (r.data.suggested as string[])?.includes(s.id),
      }))
      setSeats(flat)
      setSelectedSeats(r.data.suggested || [])
    }).catch(() => {
      setSeats(buildFallbackSeats())
      const aiRows = buildFallbackSeats().filter(s => s.isAiPick).map(s => s.id)
      setSelectedSeats(aiRows.slice(0, 2))
    }).finally(() => setLoading(false))

    api.get(`/showtimes/${showtimeId}`).then(r => setShowtime(r.data)).catch(() => {})
  }, [showtimeId])

  // WebSocket for real-time seat updates
  useEffect(() => {
    if (!showtimeId) return
    const ws = new WebSocket(`${WS_BASE}/ws/seats/${showtimeId}`)
    wsRef.current = ws
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data)
        if (msg.type === 'seats_booked' && Array.isArray(msg.seats)) {
          setSeats(prev => prev.map(s =>
            msg.seats.includes(s.id) ? { ...s, status: 'booked' as const } : s
          ))
          setSelectedSeats(prev => prev.filter(id => !msg.seats.includes(id)))
          setLiveUpdate(`${msg.seats.length} seat(s) just booked by another user`)
          setTimeout(() => setLiveUpdate(null), 4000)
        }
      } catch {}
    }
    const ping = setInterval(() => { if (ws.readyState === WebSocket.OPEN) ws.send('ping') }, 25000)
    return () => { clearInterval(ping); ws.close() }
  }, [showtimeId])

  // Countdown timer for hold
  useEffect(() => {
    if (!holdInfo?.expires_at) return
    const tick = setInterval(() => {
      const expiresAtStr = holdInfo.expires_at.endsWith('Z') ? holdInfo.expires_at : holdInfo.expires_at + 'Z'
      const secs = Math.max(0, Math.round((new Date(expiresAtStr).getTime() - Date.now()) / 1000))
      setSecondsLeft(secs)
      if (secs === 0) clearInterval(tick)
    }, 1000)
    return () => clearInterval(tick)
  }, [holdInfo])

  const toggleSeat = useCallback((id: string) => {
    setSelectedSeats(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }, [])

  const holdSeats = async () => {
    if (selectedSeats.length === 0) return
    setLoadingHold(true)
    try {
      const holdRes = await api.post(`/showtimes/${showtimeId}/holds`, {
        seats: selectedSeats, session_key: SESSION_KEY,
      })
      setHoldInfo(holdRes.data)
      const pRes = await api.get(`/showtimes/${showtimeId}/pricing`, {
        params: { hold_token: holdRes.data.hold_token },
      })
      setPricing(pRes.data)
      navigate('/checkout', {
        state: {
          showtimeId, seats: selectedSeats,
          holdToken: holdRes.data.hold_token,
          expiresAt: holdRes.data.expires_at.endsWith('Z') ? holdRes.data.expires_at : holdRes.data.expires_at + 'Z',
          total: pRes.data.total,
          showtime,
          sessionKey: SESSION_KEY,
        },
      })
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Could not hold seats. Try again.')
    } finally {
      setLoadingHold(false)
    }
  }

  const totalPrice = selectedSeats.reduce((sum, id) => {
    const s = seats.find(x => x.id === id)
    return sum + (s?.price || 360)
  }, 0)

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface-base)', padding: '24px 16px' }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>

        {/* Back button */}
        <button className="btn btn-ghost btn-sm" style={{ marginBottom: 16 }} onClick={() => navigate(-1)}>
          ← Back
        </button>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
          <div>
            <p className="eyebrow">Select Seats</p>
            <h1 style={{ fontSize: 28, fontWeight: 800, fontFamily: "'Space Grotesk',sans-serif", marginTop: 4 }}>
              {(showtime as any)?.movie_title || 'Coolie'}
            </h1>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 4 }}>
              {(showtime as any)?.theatre_name || 'PVR Orion'} · {(showtime as any)?.screen_name || 'Screen 1'} ·{' '}
              {showtime?.start_time
                ? new Date((showtime as any).start_time).toLocaleString([], { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
                : 'Today'}
            </p>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>{selectedSeats.length} seats selected</div>
            <div style={{ fontSize: 28, fontWeight: 800, color: '#F5A623', fontFamily: "'Space Grotesk',sans-serif" }}>
              ₹{totalPrice}
            </div>
          </div>
        </div>

        {/* Live seat update notification */}
        {liveUpdate && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            style={{
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 10,
              padding: '10px 14px',
              marginBottom: 12,
              fontSize: 13,
              color: '#EF4444',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            🔴 <strong>Live update:</strong> {liveUpdate}
          </motion.div>
        )}

        {/* AI recommendation strip */}
        <div className="notif-bar" style={{ marginBottom: 20 }}>
          <span>🤖</span>
          <span style={{ fontSize: 13 }}>AI highlighted best center seats (E5–E9). Grouped for 2, 62% screen distance, optimal viewing angle.</span>
        </div>

        {/* Seat map */}
        <div style={{
          background: 'var(--surface-02)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 16,
          padding: 24,
          marginBottom: 20,
          overflowX: 'auto',
        }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>Loading seat map…</div>
          ) : (
            <SeatMap seats={seats} selectedSeats={selectedSeats} onToggle={toggleSeat} />
          )}
        </div>

        {/* Seat type legend pricing */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px,1fr))', gap: 10, marginBottom: 20 }}>
          {[
            { type: 'Standard', price: 360, color: '#8FD6C8' },
            { type: 'Recliner', price: 620, color: '#F5A623' },
            { type: 'Wheelchair', price: 240, color: '#22C55E' },
          ].map(t => (
            <div key={t.type} style={{
              background: 'var(--surface-02)', border: '1px solid var(--border-subtle)',
              borderRadius: 10, padding: '10px 14px',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{t.type}</span>
              <span style={{ fontWeight: 700, color: t.color, fontSize: 14 }}>₹{t.price}</span>
            </div>
          ))}
        </div>

        {/* Confirm button */}
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          className="btn btn-primary btn-lg"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={holdSeats}
          disabled={selectedSeats.length === 0 || loadingHold}
        >
          {loadingHold ? 'Locking seats…' : `Hold ${selectedSeats.length} Seat${selectedSeats.length !== 1 ? 's' : ''} · ₹${totalPrice} →`}
        </motion.button>
      </div>
    </div>
  )
}
