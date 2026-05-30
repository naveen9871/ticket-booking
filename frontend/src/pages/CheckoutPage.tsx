import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import api from '../api'
import { useAuth } from '../hooks/useAuth'

interface LocationState {
  showtimeId: string
  seats: string[]
  holdToken: string
  expiresAt: string
  total: number
  showtime: Record<string, unknown>
  sessionKey: string
}

export default function CheckoutPage() {
  const { state } = useLocation() as { state: LocationState | null }
  const navigate = useNavigate()
  const { isLoggedIn } = useAuth()
  const [paymentMethod, setPaymentMethod] = useState<'upi' | 'card' | 'wallet' | ''>('')
  const [upiId, setUpiId] = useState('')
  const [loading, setLoading] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState<number>(600)

  useEffect(() => {
    if (!state) { navigate('/'); return }
    const target = new Date(state.expiresAt || Date.now() + 600000).getTime()
    const tick = setInterval(() => {
      const secs = Math.max(0, Math.round((target - Date.now()) / 1000))
      setSecondsLeft(secs)
      if (secs === 0) clearInterval(tick)
    }, 1000)
    return () => clearInterval(tick)
  }, [state, navigate])

  if (!state) return null

  const minutes = Math.floor(secondsLeft / 60)
  const seconds = secondsLeft % 60
  const isExpired = secondsLeft === 0

  const confirm = async () => {
    if (!paymentMethod) { alert('Choose a payment method.'); return }
    if (!isLoggedIn) { navigate('/login', { state: { from: '/checkout' } }); return }
    setLoading(true)
    try {
      const res = await api.post('/assistant/confirm', {
        showtime_id: state.showtimeId,
        seats: state.seats,
        hold_token: state.holdToken,
        session_key: state.sessionKey,
      })
      navigate(`/ticket/${res.data.booking.id}`)
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Booking failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface-base)', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '32px 16px' }}>
      <div style={{ width: '100%', maxWidth: 560 }}>

        <button className="btn btn-ghost btn-sm" style={{ marginBottom: 20 }} onClick={() => navigate(-1)}>← Back</button>

        <p className="eyebrow">Checkout</p>
        <h1 style={{ fontSize: 32, fontWeight: 800, fontFamily: "'Space Grotesk',sans-serif", marginBottom: 24, marginTop: 4 }}>
          Confirm booking
        </h1>

        {/* Hold timer */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: isExpired ? 'rgba(239,68,68,0.1)' : 'rgba(245,166,35,0.08)',
          border: `1px solid ${isExpired ? 'rgba(239,68,68,0.4)' : 'rgba(245,166,35,0.35)'}`,
          borderRadius: 12, padding: '12px 16px', marginBottom: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 20 }}>{isExpired ? '⏰' : '🔒'}</span>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14, color: isExpired ? '#EF4444' : '#F5A623' }}>
                {isExpired ? 'Hold expired!' : 'Seats held for you'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                {isExpired ? 'Go back and choose seats again.' : 'Complete payment before the hold expires.'}
              </div>
            </div>
          </div>
          {!isExpired && (
            <div className="checkout-hold-countdown" style={{ fontSize: 24, fontWeight: 800, color: '#F5A623', fontFamily: "'Space Grotesk',sans-serif" }}>
              {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
            </div>
          )}
        </div>

        {/* Booking summary */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 20, marginBottom: 20 }}
        >
          <p className="eyebrow" style={{ marginBottom: 14 }}>Booking Summary</p>
          {[
            ['Movie', (state.showtime as any)?.movie_title || 'Coolie'],
            ['Theatre', (state.showtime as any)?.theatre_name || 'PVR Orion'],
            ['Screen', (state.showtime as any)?.screen_name || 'Screen 1'],
            ['Format', (state.showtime as any)?.format || 'IMAX'],
            ['Showtime', state.showtime?.start_time ? new Date((state.showtime as any).start_time).toLocaleString([], { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'Today 7:30 PM'],
            ['Seats', state.seats.join(', ')],
          ].map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '9px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: 14 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
              <span style={{ fontWeight: 600, textAlign: 'right', maxWidth: '60%' }}>{v}</span>
            </div>
          ))}
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '14px 0 0', fontSize: 18 }}>
            <span style={{ fontWeight: 700 }}>Total</span>
            <span style={{ fontWeight: 800, color: '#F5A623', fontSize: 24, fontFamily: "'Space Grotesk',sans-serif" }}>₹{state.total || (state.seats.length * 360)}</span>
          </div>
        </motion.div>

        {/* Payment methods */}
        <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 20, marginBottom: 24 }}>
          <p className="eyebrow" style={{ marginBottom: 14 }}>Payment Method</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: paymentMethod === 'upi' ? 16 : 0 }}>
            {[
              { id: 'upi', label: '📱 UPI', sub: 'GPay, PhonePe, Paytm' },
              { id: 'card', label: '💳 Card', sub: 'Debit or Credit' },
              { id: 'wallet', label: '👛 Wallet', sub: 'Amazon, Paytm' },
            ].map(pm => (
              <button
                key={pm.id}
                onClick={() => setPaymentMethod(pm.id as typeof paymentMethod)}
                style={{
                  padding: '12px 8px',
                  background: paymentMethod === pm.id ? 'rgba(245,166,35,0.12)' : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${paymentMethod === pm.id ? 'rgba(245,166,35,0.5)' : 'rgba(255,255,255,0.1)'}`,
                  borderRadius: 10, cursor: 'pointer', textAlign: 'center', transition: 'all 0.15s',
                }}
              >
                <div style={{ fontSize: 18, marginBottom: 4 }}>{pm.label}</div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{pm.sub}</div>
              </button>
            ))}
          </div>
          {paymentMethod === 'upi' && (
            <div>
              <label className="input-label">UPI ID</label>
              <input className="input" placeholder="yourname@upi" value={upiId} onChange={e => setUpiId(e.target.value)} />
            </div>
          )}
        </div>

        {!isLoggedIn && (
          <div className="notif-bar" style={{ marginBottom: 16 }}>
            <span>🔑</span>
            <span>Login required to confirm booking</span>
            <button className="btn btn-primary btn-sm" style={{ marginLeft: 'auto' }} onClick={() => navigate('/login')}>Login</button>
          </div>
        )}

        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          className="btn btn-primary btn-lg"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={confirm}
          disabled={loading || isExpired || !paymentMethod}
        >
          {loading ? 'Confirming booking…' : isExpired ? 'Hold expired — go back' : '✓ Confirm & Pay Now'}
        </motion.button>

        <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', marginTop: 12 }}>
          🔒 Secured by Ticketly AI · PCI-safe transaction
        </p>
      </div>
    </div>
  )
}
