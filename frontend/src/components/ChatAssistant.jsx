import React, { useState, useEffect, useRef } from 'react'
import api from '../api'

const ChatAssistant = ({ token, city }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hi! I can find movies, suggest seats, and handle your bookings. What are you in the mood for?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [context, setContext] = useState({ seat_count: 2, city: city || null })
  const [seatMap, setSeatMap] = useState(null)
  const [activeShowtime, setActiveShowtime] = useState(null)
  const [selectedSeats, setSelectedSeats] = useState([])
  const chatRef = useRef(null)

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [messages])

  useEffect(() => {
    setContext((prev) => ({ ...prev, city: city || null }))
  }, [city])

  const addMessage = (role, text, data = null) => {
    setMessages((prev) => [...prev, { role, text, data }])
  }

  const handleSend = async () => {
    if (!input.trim()) return
    const text = input
    setInput('')
    addMessage('user', text)
    
    const isBookingIntent = /book|ticket|confirm|buy/i.test(text)

    setLoading(true)
    try {
      if (!token && isBookingIntent) {
        addMessage('assistant', 'You can browse movies without login. To place a booking, please login.')
        setLoading(false)
        return
      }
      const res = await api.post('/assistant/chat', { message: text, context })
      const { type, data, message } = res.data

      if (type === 'message') {
        addMessage('assistant', message)
      } else if (type === 'search_results') {
        const count = data.movies?.length || 0
        if (count > 0) {
          const titles = data.movies.map((m) => m.title).join(', ')
          addMessage('assistant', `Found ${count} movies: ${titles}. Want showtimes for one of these?`, data)
        } else {
          addMessage('assistant', 'I could not find matching movies. Try another title or city.')
        }
      } else if (type === 'movie_list') {
        const titles = data.map((m) => m.title).join(', ')
        addMessage('assistant', `Now showing: ${titles}. Want showtimes for any of these?`, data)
      } else if (type === 'showtimes') {
        addMessage('assistant', 'Here are the best available showtimes:', { _kind: 'showtimes', items: data })
      } else if (type === 'recommendations') {
        addMessage('assistant', "Here are some personalized picks for you:", { _kind: 'recommendations', items: data })
      } else if (type === 'seat_selection') {
        addMessage('assistant', `I've found the best seats: ${data.seats.join(', ')}. Would you like to confirm?`, data)
      } else if (type === 'booking_proposal') {
        const theatre = data.details?.theatre
        const movie = data.details?.movie
        const when = data.details?.start_time ? new Date(data.details.start_time).toLocaleString() : 'soon'
        const venue = theatre ? `${theatre.name}, ${theatre.city}` : 'selected theatre'
        setContext({
          ...context,
          showtime_id: data.showtime_id,
          seats: data.seats
        })
        addMessage(
          'assistant',
          `Proposed ${movie?.title || 'movie'} at ${venue} on ${when}. Seats ${data.seats.join(', ')}. Price $${data.price.price}. Confirm?`,
          {
            ...data,
            _kind: 'booking_proposal',
            steps: [
              'Matched your movie request',
              city ? `Filtered showtimes in ${city}` : 'Selected best available showtime',
              `Auto-selected ${data.seats.length} seats`,
              'Calculated dynamic price',
              'Ready to confirm booking'
            ]
          }
        )
      } else if (type === 'booking_confirmed') {
        addMessage('assistant', `Booked! Your booking id is ${data.booking_id}.`)
      } else {
        addMessage('assistant', 'I processed that. Anything else?')
      }
    } catch (e) {
      addMessage('assistant', 'Sorry, I encountered an error. Please try again.')
    }
    setLoading(false)
  }

  const handleConfirm = async (proposal) => {
    try {
      const res = await api.post('/assistant/confirm', {
        showtime_id: proposal.showtime_id,
        seats: proposal.seats
      })
      addMessage('assistant', `Success! Booking #${res.data.booking.id} confirmed. Enjoy your movie!`)
    } catch (e) {
      addMessage('assistant', 'Failed to confirm booking.')
    }
  }

  const handleChooseShowtime = async (showtime) => {
    const id = showtime.showtime_id || showtime.id
    setActiveShowtime(showtime)
    const res = await api.get(`/showtimes/${id}/seats`, { params: { count: context.seat_count } })
    setSeatMap(res.data.seat_map)
    setSelectedSeats(res.data.suggested || [])
    addMessage('assistant', 'I’ve opened the seat map. Pick seats or confirm the suggested ones.')
  }

  const toggleSeat = (seatId) => {
    setSelectedSeats((prev) => {
      if (prev.includes(seatId)) {
        return prev.filter((s) => s !== seatId)
      }
      return [...prev, seatId]
    })
  }

  const confirmSeats = async () => {
    if (!activeShowtime || selectedSeats.length === 0) return
    const res = await api.post('/assistant/confirm', {
      showtime_id: activeShowtime.showtime_id || activeShowtime.id,
      seats: selectedSeats
    })
    addMessage('assistant', `Booked! Your booking id is ${res.data.booking.id}.`)
    setSeatMap(null)
    setActiveShowtime(null)
    setSelectedSeats([])
  }

  return (
    <>
      <div className="chat-messages" ref={chatRef}>
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role === 'user' ? 'user' : 'ai'}`}>
            {m.text}
            {m.data?._kind === 'recommendations' && (
              <div className="rec-grid">
                {m.data.items.slice(0, 6).map((movie) => (
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
            {m.data?._kind === 'showtimes' && (
              <div className="showtime-grid">
                {m.data.items.slice(0, 8).map((s) => (
                  <div key={s.showtime_id || s.id} className="showtime-card-mini">
                    <div className="showtime-time">{new Date(s.start_time).toLocaleString()}</div>
                    <div className="showtime-meta">{s.theatre_name} • {s.city}</div>
                    <div className="showtime-meta">{s.format} • ₹{Math.round(s.price || s.base_price || 0)}</div>
                    <button className="ghost small" onClick={() => handleChooseShowtime(s)}>Choose</button>
                  </div>
                ))}
              </div>
            )}
            {m.data?._kind === 'booking_proposal' && (
              <div className="agent-steps">
                <div className="steps-title">Agent Steps</div>
                <ul>
                  {m.data.steps?.map((s, idx) => (
                    <li key={idx}>{s}</li>
                  ))}
                </ul>
                <div style={{ marginTop: '0.75rem' }}>
                  <button className="primary" onClick={() => handleConfirm(m.data)}>Confirm Now</button>
                </div>
              </div>
            )}
          </div>
        ))}
        {loading && <div className="message ai">...</div>}
      </div>
      {seatMap && (
        <div className="seat-map">
          <div className="seat-map-header">
            <strong>Select Seats</strong>
            <span className="muted">{selectedSeats.join(', ') || 'None selected'}</span>
          </div>
          <div className="seat-grid">
            {seatMap.map((row, ri) => (
              <div key={ri} className="seat-row">
                {row.map((seat) => {
                  const isBooked = seat.status === 'BOOKED'
                  const isSelected = selectedSeats.includes(seat.id)
                  return (
                    <button
                      key={seat.id}
                      disabled={isBooked}
                      className={`seat ${isBooked ? 'booked' : ''} ${isSelected ? 'selected' : ''}`}
                      onClick={() => toggleSeat(seat.id)}
                    >
                      {seat.id}
                    </button>
                  )
                })}
              </div>
            ))}
          </div>
          <button className="primary" onClick={confirmSeats} disabled={selectedSeats.length === 0}>
            Confirm Seats
          </button>
        </div>
      )}
      <div className="chat-input-wrap">
        <div className="chat-input">
          <input 
            placeholder="Search, book, or ask..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button onClick={handleSend} disabled={loading}>Send</button>
        </div>
      </div>
    </>
  )
}

export default ChatAssistant
