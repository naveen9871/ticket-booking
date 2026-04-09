import React, { useState } from 'react'
import api, { setToken } from '../api'

export default function Login({ onLogin }) {
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [step, setStep] = useState('phone') // phone, otp
  const [loading, setLoading] = useState(false)

  const handleStartOtp = async () => {
    setLoading(true)
    try {
      const res = await api.post('/auth/otp/start', null, { params: { phone } })
      if (res.data.sent) {
        alert(`Demo OTP: ${res.data.otp_debug}`)
        setStep('otp')
      }
    } catch (e) {
      alert('Error sending OTP')
    }
    setLoading(false)
  }

  const handleVerifyOtp = async () => {
    setLoading(true)
    try {
      const res = await api.post('/auth/otp/verify', null, { params: { phone, otp } })
      setToken(res.data.access_token)
      onLogin(res.data)
    } catch (e) {
      alert('Invalid OTP')
    }
    setLoading(false)
  }

  const handleGoogleLogin = () => {
    window.location.href = `${import.meta.env.VITE_API_BASE_URL}/auth/google/login`
  }

  return (
    <div className="page" style={{ maxWidth: '400px', textAlign: 'center' }}>
      <h1 style={{ fontSize: '2.5rem' }}>Welcome Back</h1>
      <p className="subtitle">Login to your cinematic world</p>
      
      <div className="hero-card" style={{ marginTop: '2rem' }}>
        {step === 'phone' ? (
          <>
            <input
              className="chat-input"
              style={{ width: '100%', marginBottom: '1rem', padding: '1rem', borderRadius: '12px' }}
              placeholder="Mobile Number"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
            <button className="primary" style={{ width: '100%' }} onClick={handleStartOtp} disabled={loading}>
              {loading ? 'Sending...' : 'Get OTP'}
            </button>
          </>
        ) : (
          <>
            <input
              className="chat-input"
              style={{ width: '100%', marginBottom: '1rem', padding: '1rem', borderRadius: '12px' }}
              placeholder="Enter 6-digit OTP"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
            />
            <button className="primary" style={{ width: '100%' }} onClick={handleVerifyOtp} disabled={loading}>
              {loading ? 'Verifying...' : 'Login'}
            </button>
            <button className="ghost" style={{ marginTop: '1rem' }} onClick={() => setStep('phone')}>
              Back
            </button>
          </>
        )}

        <div style={{ margin: '2rem 0', color: 'var(--text-muted)' }}>OR</div>

        <button className="ghost" style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }} onClick={handleGoogleLogin}>
          <img src="https://www.google.com/favicon.ico" width="16" />
          Continue with Google
        </button>
      </div>
    </div>
  )
}
