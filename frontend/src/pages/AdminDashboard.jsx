import React, { useState } from 'react'
import api from '../api'

export default function AdminDashboard() {
  const [message, setMessage] = useState('')
  const [chat, setChat] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!message) return
    const userMsg = { role: 'user', content: message }
    setChat([...chat, userMsg])
    setMessage('')
    setLoading(true)
    
    try {
      const res = await api.post('/admin/chat', { message })
      const aiMsg = { role: 'ai', content: res.data.message || res.data.error }
      setChat((prev) => [...prev, aiMsg])
    } catch (e) {
      setChat((prev) => [...prev, { role: 'ai', content: 'Connection error' }])
    }
    setLoading(false)
  }

  return (
    <div className="page" style={{ maxWidth: '800px' }}>
      <p className="eyebrow">Admin Ops</p>
      <h1>Operations Assistant</h1>
      <p className="subtitle">Update movie content or adjust prices using natural language.</p>

      <div className="hero-card" style={{ height: '500px', display: 'flex', flex_direction: 'column' }}>
        <div style={{ flex: 1, overflowY: 'auto', marginBottom: '1rem', paddingRight: '0.5rem' }}>
          {chat.length === 0 && (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Try: "Increase prices for Dune by 10% for the weekend" or "Generate a description for Star Wars"
            </div>
          )}
          {chat.map((m, i) => (
            <div key={i} className={`message ${m.role === 'user' ? 'user' : 'ai'}`} style={{ marginBottom: '1rem' }}>
              {m.content}
            </div>
          ))}
          {loading && <div className="message ai">Thinking...</div>}
        </div>
        <div className="chat-input" style={{ width: '100%' }}>
          <input 
            placeholder="What needs to change?" 
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button onClick={handleSend} disabled={loading}>Run</button>
        </div>
      </div>
    </div>
  )
}
