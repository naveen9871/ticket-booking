import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { setToken } from '../api'

export default function Login({ onLogin }) {
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [step, setStep] = useState('phone')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleStartOtp = async () => {
    setLoading(true)
    try {
      const res = await api.post('/auth/otp/start', null, { params: { phone } })
      if (res.data.sent) {
        alert(`Demo OTP: ${res.data.otp_debug}`)
        setStep('otp')
      }
    } catch (error) {
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
      navigate('/')
    } catch (error) {
      alert('Invalid OTP')
    }
    setLoading(false)
  }

  const handleGoogleLogin = () => {
    window.location.href = `${import.meta.env.VITE_API_BASE_URL}/auth/google/login`
  }

  return (
    <div className="auth-page">
      <div className="auth-panel">
        <div className="auth-copy">
          <p className="eyebrow">Member Access</p>
          <h1>Unlock instant checkout, ticket history, and smarter recommendations.</h1>
          <p className="subtitle">
            Sign in once and your next booking becomes a two-step flow: pick the show, confirm the seats.
          </p>
          <div className="auth-benefits">
            <div className="benefit-card">
              <strong>Faster Checkout</strong>
              <span>Assistant-led booking with saved context.</span>
            </div>
            <div className="benefit-card">
              <strong>mTicket Access</strong>
              <span>Retrieve QR-based tickets right inside the app.</span>
            </div>
            <div className="benefit-card">
              <strong>Personalized Picks</strong>
              <span>Better discovery tuned to your city and language.</span>
            </div>
          </div>
        </div>

        <div className="auth-card">
          <h2>{step === 'phone' ? 'Login with OTP' : 'Verify OTP'}</h2>
          <p className="muted">
            {step === 'phone'
              ? 'Use your mobile number to start a secure session.'
              : 'Enter the 6-digit code you received.'}
          </p>

          {step === 'phone' ? (
            <>
              <input
                className="auth-input"
                placeholder="Mobile Number"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
              />
              <button className="primary auth-button" onClick={handleStartOtp} disabled={loading}>
                {loading ? 'Sending...' : 'Get OTP'}
              </button>
            </>
          ) : (
            <>
              <input
                className="auth-input"
                placeholder="Enter 6-digit OTP"
                value={otp}
                onChange={(event) => setOtp(event.target.value)}
              />
              <button className="primary auth-button" onClick={handleVerifyOtp} disabled={loading}>
                {loading ? 'Verifying...' : 'Login'}
              </button>
              <button className="ghost auth-button" onClick={() => setStep('phone')}>
                Back
              </button>
            </>
          )}

          <div className="auth-divider">or continue with</div>

          <button className="ghost auth-google" onClick={handleGoogleLogin}>
            <img src="https://www.google.com/favicon.ico" width="16" height="16" alt="Google" />
            Google
          </button>
        </div>
      </div>
    </div>
  )
}
