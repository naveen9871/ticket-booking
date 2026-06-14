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

declare global {
  interface Window {
    Razorpay: any
  }
}

function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (window.Razorpay) { resolve(true); return }
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.onload = () => resolve(true)
    script.onerror = () => resolve(false)
    document.body.appendChild(script)
  })
}

export default function CheckoutPage() {
  const { state } = useLocation() as { state: LocationState | null }
  const navigate = useNavigate()
  const { isLoggedIn, user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState<number>(600)
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success' | 'failed'>('idle')

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

  const handleRazorpay = async () => {
    if (!isLoggedIn) { navigate('/login', { state: { from: '/checkout' } }); return }
    if (isExpired) { alert('Hold expired. Please go back and select seats again.'); return }

    setLoading(true)
    setPaymentStatus('processing')

    const loaded = await loadRazorpayScript()
    if (!loaded) {
      alert('Razorpay failed to load. Check your internet connection.')
      setLoading(false)
      setPaymentStatus('idle')
      return
    }

    try {
      const orderRes = await api.post('/payments/create-order', {
        showtime_id: state.showtimeId,
        seats: state.seats,
        hold_token: state.holdToken,
        session_key: state.sessionKey,
      })
      const order = orderRes.data

      const options = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: order.name,
        description: order.description,
        order_id: order.order_id,
        prefill: {
          name: (user as any)?.full_name || '',
          email: (user as any)?.email || '',
          contact: (user as any)?.phone || '',
        },
        theme: { color: '#F5A623' },
        modal: {
          ondismiss: () => {
            setLoading(false)
            setPaymentStatus('idle')
          },
        },
        handler: async (response: {
          razorpay_payment_id: string
          razorpay_order_id: string
          razorpay_signature: string
        }) => {
          try {
            const verifyRes = await api.post('/payments/verify', {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
              showtime_id: state.showtimeId,
              seats: state.seats,
              hold_token: state.holdToken,
              session_key: state.sessionKey,
            })
            setPaymentStatus('success')
            navigate(`/ticket/${verifyRes.data.booking_id}`)
          } catch (e: any) {
            setPaymentStatus('failed')
            alert(e?.response?.data?.detail || 'Payment verification failed. Contact support.')
          } finally {
            setLoading(false)
          }
        },
      }

      const rzp = new window.Razorpay(options)
      rzp.on('payment.failed', (response: any) => {
        setPaymentStatus('failed')
        setLoading(false)
        alert(`Payment failed: ${response.error.description}`)
      })
      rzp.open()
    } catch (e: any) {
      setPaymentStatus('failed')
      setLoading(false)
      alert(e?.response?.data?.detail || 'Could not initiate payment. Try again.')
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
            <div style={{ fontSize: 24, fontWeight: 800, color: '#F5A623', fontFamily: "'Space Grotesk',sans-serif" }}>
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
            ['Movie', (state.showtime as any)?.movie_title || 'Your Movie'],
            ['Theatre', (state.showtime as any)?.theatre_name || '—'],
            ['Screen', (state.showtime as any)?.screen_name || '—'],
            ['Format', (state.showtime as any)?.format || '—'],
            ['Showtime', state.showtime?.start_time
              ? new Date((state.showtime as any).start_time).toLocaleString([], { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
              : '—'],
            ['Seats', state.seats.join(', ')],
          ].map(([k, v]) => (
            <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '9px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: 14 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
              <span style={{ fontWeight: 600, textAlign: 'right', maxWidth: '60%' }}>{v}</span>
            </div>
          ))}
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '14px 0 0', fontSize: 18 }}>
            <span style={{ fontWeight: 700 }}>Total</span>
            <span style={{ fontWeight: 800, color: '#F5A623', fontSize: 24, fontFamily: "'Space Grotesk',sans-serif" }}>
              ₹{state.total || (state.seats.length * 360)}
            </span>
          </div>
        </motion.div>

        {/* Razorpay trust badge */}
        <div style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 12,
          padding: '14px 18px',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}>
          <span style={{ fontSize: 24 }}>🔒</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>Secure Payment via Razorpay</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
              Supports UPI · Cards · Net Banking · Wallets · EMI · Pay Later
            </div>
          </div>
        </div>

        {/* Payment status banner */}
        {paymentStatus === 'failed' && (
          <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '12px 16px', marginBottom: 16, fontSize: 13, color: '#EF4444' }}>
            Payment failed. Please try again or use a different payment method.
          </div>
        )}

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
          style={{ width: '100%', justifyContent: 'center', fontSize: 16 }}
          onClick={handleRazorpay}
          disabled={loading || isExpired || !isLoggedIn}
        >
          {loading
            ? '⏳ Opening payment…'
            : isExpired
            ? 'Hold expired — go back'
            : `Pay ₹${state.total || state.seats.length * 360} via Razorpay →`}
        </motion.button>

        <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', marginTop: 12 }}>
          🔒 256-bit SSL · PCI-DSS compliant · Powered by Razorpay
        </p>
      </div>
    </div>
  )
}
