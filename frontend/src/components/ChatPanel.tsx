import { useState, useRef, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import api from '../api'
import { useNavigate } from 'react-router-dom'

const STARTERS = [
  'Find 4 seats for Coolie near Whitefield',
  'Show Dolby Atmos options under ₹500 tonight',
  'Alert me when Pushpa 3 bookings open',
  'Recommend theatres based on my history',
]

const createSessionKey = () =>
  typeof window !== 'undefined' && window.crypto?.randomUUID
    ? `guest-${window.crypto.randomUUID()}`
    : `guest-${Math.random().toString(36).slice(2, 12)}`

interface Message {
  id: string
  role: 'user' | 'assistant'
  text: string
  data?: Record<string, unknown>
  trace?: Array<{ agent: string; detail: string }>
}

interface Props {
  city: string
  token: string | null
  mobileOpen?: boolean
  onClose?: () => void
}

export function ChatPanel({ city, token, mobileOpen, onClose }: Props) {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([{
    id: '0',
    role: 'assistant',
    text: `Hi! I'm your AI booking concierge. Describe what you need and I'll compare theatres, seats, pricing, and availability. I will not hold seats or start payment until you confirm.`,
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionKey] = useState(createSessionKey)
  const [context, setContext] = useState<Record<string, unknown>>({ seat_count: 2, city, session_key: sessionKey })
  const bodyRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight
  }, [messages, loading])

  useEffect(() => {
    setContext(prev => ({ ...prev, city }))
  }, [city])

  const addMsg = (role: Message['role'], text: string, data?: Record<string, unknown>, trace?: Message['trace']) => {
    setMessages(prev => [...prev, { id: crypto.randomUUID(), role, text, data, trace }])
  }

  const send = async (raw: string) => {
    if (!raw.trim() || loading) return
    const text = raw.trim()
    setInput('')
    addMsg('user', text)
    setLoading(true)
    try {
      const res = await api.post('/assistant/chat', { message: text, context })
      const { type, data, message, trace, context: nextCtx } = res.data
      if (nextCtx) setContext(prev => ({ ...prev, ...nextCtx, session_key: sessionKey }))

      if (type === 'agent_plan') {
        addMsg('assistant', message || 'Here are your personalised booking plans:', { _kind: 'agent_plan', ...data }, trace)
      } else if (type === 'showtimes') {
        addMsg('assistant', 'Best matching showtimes right now:', { _kind: 'showtimes', items: data }, trace)
      } else {
        addMsg('assistant', message || 'Done.', data, trace)
      }
    } catch {
      addMsg('assistant', 'Something went wrong while checking availability. Please try again, and I will rebuild the plan safely.')
    }
    setLoading(false)
  }

  return (
    <div className="chat-shell" style={{ height: '100%' }}>
      {/* Header */}
      <div className="chat-head">
        <div>
            <p className="eyebrow">AI Concierge</p>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginTop: 2, color: '#EDF4F2' }}>Booking Agent</h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="pill pill-teal">
            <span className="live-dot" style={{ width: 5, height: 5 }} /> Live
          </span>
          {onClose && (
            <button onClick={onClose} className="btn btn-ghost btn-sm">✕</button>
          )}
        </div>
      </div>

      {/* Quick starters */}
      <div style={{ padding: '10px 14px 0', display: 'flex', flexWrap: 'wrap', gap: 6, flexShrink: 0 }}>
        {STARTERS.map(s => (
          <button
            key={s}
            onClick={() => send(s.replace(/^[^\s]+ /, ''))}
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 999,
              padding: '4px 10px',
              fontSize: 11,
              color: 'rgba(237,244,242,0.7)',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >{s}</button>
        ))}
      </div>

      {/* Messages */}
      <div className="chat-body" ref={bodyRef}>
        {messages.map(m => (
          <motion.div
            key={m.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className={`bubble ${m.role}`}
          >
            <p style={{ margin: 0, fontSize: 14, lineHeight: 1.55 }}>{m.text}</p>

            {/* Agent plan cards */}
            {m.data?._kind === 'agent_plan' && Array.isArray((m.data as any).plans) && (
              <div className="agent-plan-grid">
                {((m.data as any).plans as any[]).slice(0, 3).map((plan: any, i: number) => (
                  <div key={i} className="plan-card">
                    <div className="plan-chip">{plan.plan_type || 'BALANCED'}</div>
                    <div style={{ fontWeight: 700, fontSize: 14, color: '#EDF4F2', marginBottom: 4 }}>{plan.title}</div>
                    <p style={{ fontSize: 12, color: 'rgba(237,244,242,0.6)', margin: '0 0 6px' }}>{plan.summary}</p>
                    <div className="plan-price">₹{Math.round(plan.estimated_total || 0)}</div>
                    <div className="plan-rationale">
                      {((plan.rationale || []) as string[]).slice(0, 2).map((r: string) => (
                        <span key={r}>{r}</span>
                      ))}
                    </div>
                    <button
                      className="btn btn-primary btn-sm"
                      style={{ marginTop: 10, width: '100%' }}
                      onClick={() => plan.showtime_id && navigate(`/seats/${plan.showtime_id}`)}
                    >Open Seat Map →</button>
                  </div>
                ))}
              </div>
            )}

            {/* Showtime cards */}
            {m.data?._kind === 'showtimes' && Array.isArray((m.data as any).items) && (
              <div className="showtime-grid">
                {((m.data as any).items as any[]).slice(0, 6).map((s: any) => (
                  <div key={s.showtime_id || s.id} className="showtime-card-mini">
                    <div className="showtime-time">{new Date(s.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    <div className="showtime-meta">{s.theatre_name}</div>
                    <div className="showtime-meta">{s.format} · ₹{s.base_price || s.price || 0}</div>
                    <button
                      className="btn btn-primary btn-sm"
                      style={{ marginTop: 6, width: '100%' }}
                      onClick={() => navigate(`/seats/${s.showtime_id || s.id}`)}
                    >Pick Seats</button>
                  </div>
                ))}
              </div>
            )}

            {/* Agent trace */}
            {m.trace && m.trace.length > 0 && (
              <div style={{ marginTop: 10, borderTop: '1px solid rgba(255,255,255,0.07)', paddingTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {m.trace.map((step, i) => (
                  <div key={i} style={{ display: 'flex', gap: 8, fontSize: 11 }}>
                    <span style={{ color: '#8FD6C8', fontWeight: 600, flexShrink: 0 }}>{step.agent}</span>
                    <span style={{ color: 'rgba(237,244,242,0.45)' }}>{step.detail}</span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        ))}

        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="bubble assistant"
            >
              <div className="typing-dots">
                <span className="dot" /><span className="dot" /><span className="dot" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input */}
      <div className="chat-footer">
        <div className="chat-input-row">
          <textarea
            className="chat-textarea"
            placeholder="Try: Find 2 recliners for Coolie tomorrow near Whitefield..."
            value={input}
            rows={1}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}
          />
          <button
            className="btn btn-primary"
            style={{ padding: '10px 14px', flexShrink: 0 }}
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
          >
            {loading ? '…' : '→'}
          </button>
        </div>
      </div>
    </div>
  )
}
