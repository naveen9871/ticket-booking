import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { QRCodeSVG } from 'qrcode.react'
import api from '../api'

export default function TicketPage() {
  const { bookingId } = useParams<{ bookingId: string }>()
  const navigate = useNavigate()
  const [ticket, setTicket] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/bookings/${bookingId}/ticket`).then(r => setTicket(r.data)).catch(() => {
      // Fallback demo ticket
      setTicket({
        ticket: {
          movie: 'Coolie',
          theatre: 'PVR Orion IMAX',
          city: 'Bengaluru',
          screen: 'Screen 1',
          start_time: new Date(Date.now() + 3600000).toISOString(),
          seats: 'E5, E6',
          booking_id: bookingId,
        }
      })
    }).finally(() => setLoading(false))
  }, [bookingId])

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'var(--surface-base)' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ width: 40, height: 40, border: '3px solid var(--brand-teal)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin-slow 1s linear infinite', margin: '0 auto 12px' }} />
        <p style={{ color: 'var(--text-muted)' }}>Loading your ticket…</p>
      </div>
    </div>
  )

  const t = ticket?.ticket || {}
  const qrData = JSON.stringify({ booking_id: bookingId, seats: t.seats, movie: t.movie })

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface-base)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, type: 'spring' }}
        >
          {/* Ticket card */}
          <div style={{
            background: 'linear-gradient(145deg, var(--surface-02), var(--surface-03))',
            border: '1px solid rgba(245,166,35,0.3)',
            borderRadius: 20,
            overflow: 'hidden',
            boxShadow: '0 8px 48px rgba(245,166,35,0.15), 0 2px 16px rgba(0,0,0,0.5)',
          }}>
            {/* Header strip */}
            <div style={{
              background: 'linear-gradient(135deg, #F5A623, #EF4444)',
              padding: '20px 24px',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 32 }}>🎬</div>
              <div style={{ fontSize: 20, fontWeight: 900, color: '#fff', fontFamily: "'Space Grotesk',sans-serif", marginTop: 4 }}>
                mTicket Confirmed!
              </div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)', marginTop: 4 }}>
                Booking #{bookingId}
              </div>
            </div>

            {/* Perforated separator */}
            <div style={{ display: 'flex', alignItems: 'center', margin: '0 -1px' }}>
              <div style={{ width: 20, height: 20, borderRadius: '50%', background: 'var(--surface-base)', flexShrink: 0, marginLeft: -1 }} />
              <div style={{ flex: 1, borderTop: '2px dashed rgba(255,255,255,0.1)' }} />
              <div style={{ width: 20, height: 20, borderRadius: '50%', background: 'var(--surface-base)', flexShrink: 0, marginRight: -1 }} />
            </div>

            {/* Ticket details */}
            <div style={{ padding: '20px 24px' }}>
              {[
                ['Movie', t.movie || 'Coolie'],
                ['Theatre', `${t.theatre || 'PVR Orion'} · ${t.city || 'Bengaluru'}`],
                ['Screen', t.screen || 'Screen 1'],
                ['Date & Time', t.start_time ? new Date(t.start_time).toLocaleString([], { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'Today'],
                ['Seats', t.seats || 'E5, E6'],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.06)', fontSize: 14 }}>
                  <span style={{ color: 'var(--text-muted)' }}>{k}</span>
                  <span style={{ fontWeight: 600, textAlign: 'right', maxWidth: '60%' }}>{v}</span>
                </div>
              ))}
            </div>

            {/* Perforated separator */}
            <div style={{ display: 'flex', alignItems: 'center', margin: '0 -1px' }}>
              <div style={{ width: 20, height: 20, borderRadius: '50%', background: 'var(--surface-base)', flexShrink: 0, marginLeft: -1 }} />
              <div style={{ flex: 1, borderTop: '2px dashed rgba(255,255,255,0.1)' }} />
              <div style={{ width: 20, height: 20, borderRadius: '50%', background: 'var(--surface-base)', flexShrink: 0, marginRight: -1 }} />
            </div>

            {/* QR Code */}
            <div style={{ padding: '20px 24px', textAlign: 'center' }}>
              <div className="qr-wrap" style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 10, background: 'white', borderRadius: 12, padding: 16 }}>
                <QRCodeSVG value={qrData} size={140} level="H" />
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 10 }}>
                Scan at the theatre entry gate
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: 10, marginTop: 20, flexWrap: 'wrap' }}>
            <button className="btn btn-secondary" style={{ flex: 1, minWidth: 120 }} onClick={() => navigate('/')}>
              🏠 Home
            </button>
            <button className="btn btn-secondary" style={{ flex: 1, minWidth: 120 }} onClick={() => navigate('/my-bookings')}>
              🎟️ My Bookings
            </button>
            <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => window.print()}>
              📥 Download Ticket
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
