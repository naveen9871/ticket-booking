import React, { useEffect, useRef, useState } from 'react'
import api from '../api'

const QUICK_PROMPTS = [
  'Plan a premium movie night near me',
  'Find a budget-friendly movie this weekend',
  'Book 2 seats for the best rated show tonight',
]

const formatMoney = (value) => `Rs ${Math.round(value || 0)}`

const createSessionKey = () => {
  if (typeof window !== 'undefined' && window.crypto?.randomUUID) {
    return `guest-${window.crypto.randomUUID()}`
  }
  return `guest-${Math.random().toString(36).slice(2, 12)}`
}

const ChatAssistant = ({ token, city }) => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Describe the outcome you want, and I will turn it into a few bookable plans with pricing, showtimes, and seat suggestions.',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [context, setContext] = useState({ seat_count: 2, city: city || null, session_key: createSessionKey() })
  const [seatMap, setSeatMap] = useState(null)
  const [activeShowtime, setActiveShowtime] = useState(null)
  const [selectedSeats, setSelectedSeats] = useState([])
  const [showPayment, setShowPayment] = useState(false)
  const [pricing, setPricing] = useState(null)
  const [paymentMethod, setPaymentMethod] = useState('')
  const [showReview, setShowReview] = useState(false)
  const [ticket, setTicket] = useState(null)
  const [holdInfo, setHoldInfo] = useState(null)
  const chatRef = useRef(null)

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [messages])

  useEffect(() => {
    setContext((prev) => ({ ...prev, city: city || null }))
  }, [city])

  const addMessage = (role, text, data = null, trace = null) => {
    setMessages((prev) => [...prev, { role, text, data, trace }])
  }

  const mergeContext = (nextContext) => {
    if (!nextContext) return
    setContext((prev) => ({ ...prev, ...nextContext, session_key: prev.session_key || nextContext.session_key }))
  }

  const sendMessage = async (rawText) => {
    if (!rawText.trim()) return

    const text = rawText.trim()
    setInput('')
    addMessage('user', text)
    setLoading(true)

    try {
      const res = await api.post('/assistant/chat', { message: text, context })
      const { type, data, message, trace, context: nextContext } = res.data
      mergeContext(nextContext)

      if (type === 'message') {
        addMessage('assistant', message, data, trace)
      } else if (type === 'agent_plan') {
        addMessage('assistant', message, { _kind: 'agent_plan', ...data }, trace)
      } else if (type === 'showtimes') {
        addMessage('assistant', 'These are the strongest matching showtimes right now.', { _kind: 'showtimes', items: data }, trace)
      } else if (type === 'recommendations') {
        addMessage('assistant', 'These options line up well with your current taste profile.', { _kind: 'recommendations', items: data }, trace)
      } else {
        addMessage('assistant', message || 'I mapped your request into the current booking workflow.', data, trace)
      }
    } catch (error) {
      addMessage('assistant', 'Something failed while I was planning that. Please try once more.')
    }

    setLoading(false)
  }

  const handleSend = async () => {
    await sendMessage(input)
  }

  const handleChooseShowtime = async (showtime) => {
    const id = showtime.showtime_id || showtime.id
    const res = await api.get(`/showtimes/${id}/seats`, {
      params: { count: context.seat_count, session_key: context.session_key, hold_token: holdInfo?.hold_token },
    })

    setActiveShowtime(showtime)
    setSeatMap(res.data.seat_map)
    setSelectedSeats(res.data.suggested || [])
    setHoldInfo(null)
    setPricing(null)
    setShowPayment(false)
    setShowReview(false)
    setPaymentMethod('')
    setContext((prev) => ({
      ...prev,
      showtime_id: id,
      seats: res.data.suggested || [],
    }))
    addMessage('assistant', 'Seat map opened. I highlighted the best contiguous seats first, and we will place a temporary hold before payment.')
  }

  const handleChoosePlan = async (plan) => {
    const candidate = plan.metadata?.candidate || { id: plan.showtime_id }
    const showtime = {
      id: plan.showtime_id,
      movie_title: candidate.movie_title,
      theatre_name: candidate.theatre_name,
      city: candidate.city,
      screen_name: candidate.screen_name,
      start_time: candidate.start_time,
      base_price: candidate.base_price,
      format: candidate.format,
    }
    await handleChooseShowtime(showtime)
  }

  const toggleSeat = (seatId) => {
    setSelectedSeats((prev) => {
      if (prev.includes(seatId)) {
        return prev.filter((seat) => seat !== seatId)
      }
      return [...prev, seatId]
    })
  }

  const confirmSeats = async () => {
    if (!activeShowtime || selectedSeats.length === 0) return
    const id = activeShowtime.showtime_id || activeShowtime.id

    try {
      const holdRes = await api.post(`/showtimes/${id}/holds`, {
        seats: selectedSeats,
        session_key: context.session_key,
      })
      const pricingRes = await api.get(`/showtimes/${id}/pricing`, {
        params: { hold_token: holdRes.data.hold_token },
      })

      setHoldInfo(holdRes.data)
      setPricing(pricingRes.data)
      setShowPayment(true)
      setShowReview(false)
      setContext((prev) => ({
        ...prev,
        seats: selectedSeats,
        showtime_id: id,
        hold_token: holdRes.data.hold_token,
      }))
      addMessage(
        'assistant',
        `Seats ${selectedSeats.join(', ')} are locked for a short window. Review payment whenever you are ready.`,
      )
    } catch (error) {
      addMessage('assistant', error?.response?.data?.detail || 'Those seats could not be locked. Try another cluster.')
    }
  }

  const handlePayAndConfirm = async () => {
    if (!token) {
      addMessage('assistant', 'Login is required before payment confirmation.')
      return
    }
    if (!paymentMethod) {
      addMessage('assistant', 'Choose a payment method to continue.')
      return
    }
    setShowReview(true)
  }

  const finalizeBooking = async () => {
    try {
      const res = await api.post('/assistant/confirm', {
        showtime_id: activeShowtime.showtime_id || activeShowtime.id,
        seats: selectedSeats,
        hold_token: holdInfo?.hold_token,
        session_key: context.session_key,
      })
      addMessage('assistant', `Booked. Your booking id is ${res.data.booking.id}.`)
      const ticketRes = await api.get(`/bookings/${res.data.booking.id}/ticket`)
      setTicket(ticketRes.data)
      setShowReview(false)
      setShowPayment(false)
      setSeatMap(null)
      setActiveShowtime(null)
      setSelectedSeats([])
      setPricing(null)
      setPaymentMethod('')
      setHoldInfo(null)
    } catch (error) {
      addMessage('assistant', error?.response?.data?.detail || 'I could not finalize the booking yet.')
    }
  }

  const totalPrice = pricing?.total || (pricing?.price || activeShowtime?.price || activeShowtime?.base_price || 0) * selectedSeats.length

  return (
    <div className="assistant-card">
      <div className="assistant-header">
        <div>
          <p className="eyebrow">AI Concierge</p>
          <h3>Intent in. Plans out. Booking handled.</h3>
        </div>
        <span className="assistant-city">{city || 'All cities'}</span>
      </div>

      <div className="assistant-summary">
        <div>
          <strong>Seat Preference</strong>
          <span>{context.seat_count} seats</span>
        </div>
        <div>
          <strong>Mode</strong>
          <span>{token ? 'Ready for checkout' : 'Guest planning'}</span>
        </div>
      </div>

      <div className="quick-prompt-row">
        {QUICK_PROMPTS.map((prompt) => (
          <button key={prompt} className="chip" onClick={() => sendMessage(prompt)}>
            {prompt}
          </button>
        ))}
      </div>

      <div className="chat-messages" ref={chatRef}>
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role === 'user' ? 'user' : 'ai'}`}>
            {message.text}
            {message.data?._kind === 'recommendations' && (
              <div className="rec-grid">
                {message.data.items.slice(0, 6).map((movie) => (
                  <div key={movie.id} className="rec-card">
                    <img src={movie.poster_url} alt={movie.title} />
                    <div className="rec-info">
                      <strong>{movie.title}</strong>
                      <span>{movie.language} • {movie.genre}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {message.data?._kind === 'showtimes' && (
              <div className="showtime-grid">
                {message.data.items.slice(0, 8).map((showtime) => (
                  <div key={showtime.showtime_id || showtime.id} className="showtime-card-mini">
                    <div className="showtime-time">{new Date(showtime.start_time).toLocaleString()}</div>
                    <div className="showtime-meta">{showtime.theatre_name} • {showtime.city}</div>
                    <div className="showtime-meta">{showtime.format} • {formatMoney(showtime.price || showtime.base_price || 0)}</div>
                    <button className="ghost small" onClick={() => handleChooseShowtime(showtime)}>Choose</button>
                  </div>
                ))}
              </div>
            )}
            {message.data?._kind === 'agent_plan' && (
              <div className="agent-plan-stack">
                <div className="plan-intent">
                  <strong>Intent Summary</strong>
                  <span>{message.data.intent?.summary}</span>
                </div>
                <div className="agent-plan-grid">
                  {message.data.plans?.map((plan) => (
                    <div key={`${plan.plan_type}-${plan.showtime_id}`} className="plan-card">
                      <div className="plan-chip">{plan.plan_type}</div>
                      <strong>{plan.title}</strong>
                      <p>{plan.summary}</p>
                      <div className="plan-price">{formatMoney(plan.estimated_total)}</div>
                      <div className="plan-rationale">
                        {plan.rationale?.slice(0, 2).map((reason) => (
                          <span key={reason}>{reason}</span>
                        ))}
                      </div>
                      <button className="primary" onClick={() => handleChoosePlan(plan)}>Open Seats</button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {message.trace?.length > 0 && (
              <div className="agent-trace">
                {message.trace.map((step) => (
                  <div key={`${step.agent}-${step.detail}`} className="trace-item">
                    <strong>{step.agent}</strong>
                    <span>{step.detail}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="message ai">Intent agent is parsing your request, then discovery and planning are assembling options.</div>}
      </div>

      {seatMap && (
        <div className="seat-map">
          <div className="seat-map-header">
            <div>
              <strong>Select Seats</strong>
              <div className="muted">
                {activeShowtime?.theatre_name || 'Theatre'} • {activeShowtime?.screen_name || 'Screen'}
              </div>
            </div>
            <span className="muted">{selectedSeats.join(', ') || 'No seats selected'}</span>
          </div>
          <div className="screen-indicator">Screen this side</div>
          <div className="seat-legend">
            <span><i className="legend available"></i>Available</span>
            <span><i className="legend selected"></i>Selected</span>
            <span><i className="legend held"></i>Held</span>
            <span><i className="legend booked"></i>Booked</span>
          </div>
          <div className="seat-grid">
            {seatMap.map((row, rowIndex) => (
              <div key={rowIndex} className="seat-row">
                <div className="row-label">{row[0]?.id?.charAt(0) || ''}</div>
                {row.map((seat) => {
                  const isBooked = seat.status === 'BOOKED'
                  const isHeld = seat.status === 'HELD'
                  const isSelected = selectedSeats.includes(seat.id) || seat.status === 'HELD_BY_YOU'
                  return (
                    <button
                      key={seat.id}
                      disabled={isBooked || isHeld}
                      className={`seat ${isBooked ? 'booked' : ''} ${isHeld ? 'held' : ''} ${isSelected ? 'selected' : ''}`}
                      onClick={() => toggleSeat(seat.id)}
                    >
                      {seat.id.slice(1)}
                    </button>
                  )
                })}
              </div>
            ))}
          </div>
          <button className="primary" onClick={confirmSeats} disabled={selectedSeats.length === 0}>
            Lock Seats and Continue
          </button>
        </div>
      )}

      {showPayment && (
        <div className="payment-box">
          <div className="payment-row">
            <strong>Total</strong>
            <span>{formatMoney(totalPrice)}</span>
          </div>
          <div className="payment-row">
            <strong>Seats</strong>
            <span>{selectedSeats.join(', ')}</span>
          </div>
          {holdInfo?.expires_at && (
            <div className="payment-row">
              <strong>Hold Expires</strong>
              <span>{new Date(holdInfo.expires_at).toLocaleTimeString()}</span>
            </div>
          )}
          <div className="payment-methods">
            <button className={`pay-option ${paymentMethod === 'upi' ? 'active' : ''}`} onClick={() => setPaymentMethod('upi')}>UPI</button>
            <button className={`pay-option ${paymentMethod === 'card' ? 'active' : ''}`} onClick={() => setPaymentMethod('card')}>Card</button>
            <button className={`pay-option ${paymentMethod === 'wallet' ? 'active' : ''}`} onClick={() => setPaymentMethod('wallet')}>Wallet</button>
          </div>
          <button className="primary" onClick={handlePayAndConfirm}>Review Booking</button>
        </div>
      )}

      {showReview && (
        <div className="ticket-review">
          <div className="ticket-title">Review Your Ticket</div>
          <div className="ticket-row">
            <span>Movie</span>
            <strong>{activeShowtime?.movie_title || 'Movie'}</strong>
          </div>
          <div className="ticket-row">
            <span>Theatre</span>
            <strong>{activeShowtime?.theatre_name || 'Theatre'}</strong>
          </div>
          <div className="ticket-row">
            <span>Screen</span>
            <strong>{activeShowtime?.screen_name || 'Screen'}</strong>
          </div>
          <div className="ticket-row">
            <span>Showtime</span>
            <strong>{activeShowtime?.start_time ? new Date(activeShowtime.start_time).toLocaleString() : 'Showtime'}</strong>
          </div>
          <div className="ticket-row">
            <span>Seats</span>
            <strong>{selectedSeats.join(', ')}</strong>
          </div>
          <div className="ticket-row">
            <span>Amount</span>
            <strong>{formatMoney(totalPrice)}</strong>
          </div>
          <button className="primary" onClick={finalizeBooking}>Confirm Booking</button>
        </div>
      )}

      {ticket && (
        <div className="ticket-confirmation">
          <div className="ticket-title">mTicket Confirmed</div>
          <div className="ticket-row">
            <span>Movie</span>
            <strong>{ticket.ticket.movie}</strong>
          </div>
          <div className="ticket-row">
            <span>Theatre</span>
            <strong>{ticket.ticket.theatre} • {ticket.ticket.city}</strong>
          </div>
          <div className="ticket-row">
            <span>Screen</span>
            <strong>{ticket.ticket.screen}</strong>
          </div>
          <div className="ticket-row">
            <span>Showtime</span>
            <strong>{new Date(ticket.ticket.start_time).toLocaleString()}</strong>
          </div>
          <div className="ticket-row">
            <span>Seats</span>
            <strong>{ticket.ticket.seats}</strong>
          </div>
          <div className="qr-wrap">
            <img src={ticket.qr} alt="Ticket QR" />
            <div className="muted">Scan this QR at the theatre entry gate</div>
          </div>
        </div>
      )}

      <div className="chat-input-wrap">
        <div className="chat-input">
          <input
            placeholder="Try: plan a Friday night under Rs 1200 near me"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => event.key === 'Enter' && handleSend()}
          />
          <button onClick={handleSend} disabled={loading}>Send</button>
        </div>
      </div>
    </div>
  )
}

export default ChatAssistant
