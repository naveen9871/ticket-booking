import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useGoogleLogin } from '@react-oauth/google'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const { login, googleLogin, isLoggedIn } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<'login' | 'demo'>('login')

  // Redirect if already logged in
  useEffect(() => {
    if (isLoggedIn) navigate('/', { replace: true })
  }, [isLoggedIn, navigate])

  const DEMO_ACCOUNTS = [
    { label: '🎬 Demo User', email: 'user@ticketly.demo', password: 'demo123', role: 'User' },
    { label: '🛡️ Admin', email: 'admin@ticketly.demo', password: 'admin123', role: 'Super Admin' },
    { label: '🏟️ Theatre Owner', email: 'owner@ticketly.demo', password: 'owner123', role: 'Theatre Owner' },
  ]

  const handleLogin = async (e?: { preventDefault: () => void }, preEmail?: string, prePass?: string) => {
    e?.preventDefault()
    const em = preEmail ?? email
    const pw = prePass ?? password
    setError('')
    setLoading(true)
    try {
      const user = await login(em, pw)
      navigate(user.is_admin ? '/admin' : '/')
    } catch {
      setError('Invalid email or password. Try a demo account below.')
    } finally {
      setLoading(false)
    }
  }

  const loginGoogle = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setError('')
      setLoading(true)
      try {
        const user = await googleLogin(tokenResponse.access_token)
        navigate(user.is_admin ? '/admin' : '/')
      } catch (err: any) {
        setError(`Google Login failed: ${err.message || String(err)}`)
      } finally {
        setLoading(false)
      }
    },
    onError: (error) => setError(`Google Login failed: ${error.error_description || error.error || 'Unknown error'}`)
  })

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--surface-base)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 20,
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Animated BG blobs */}
      <div style={{
        position: 'absolute', top: '20%', left: '10%',
        width: 400, height: 400, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(245,166,35,0.08) 0%, transparent 70%)',
        filter: 'blur(60px)', pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', bottom: '15%', right: '10%',
        width: 350, height: 350, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(143,214,200,0.08) 0%, transparent 70%)',
        filter: 'blur(60px)', pointerEvents: 'none',
      }} />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ width: '100%', maxWidth: 420 }}
      >
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16,
            background: 'linear-gradient(135deg, #F5A623, #EF4444)',
            display: 'grid', placeItems: 'center',
            fontSize: 28, fontWeight: 900, color: '#fff',
            margin: '0 auto 12px',
            boxShadow: '0 0 32px rgba(245,166,35,0.35)',
          }}>T</div>
          <h1 style={{ fontSize: 28, fontWeight: 800, fontFamily: "'Space Grotesk',sans-serif" }}>
            Welcome to Ticketly
          </h1>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 6 }}>
            AI-powered movie ticket booking
          </p>
        </div>

        {/* Card */}
        <div className="glass" style={{ padding: 28 }}>
          {/* Tab toggle */}
          <div style={{ display: 'flex', gap: 4, marginBottom: 24, background: 'rgba(255,255,255,0.04)', borderRadius: 10, padding: 4 }}>
            {(['login', 'demo'] as const).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                style={{
                  flex: 1, padding: '8px 0',
                  background: mode === m ? 'rgba(245,166,35,0.15)' : 'transparent',
                  border: `1px solid ${mode === m ? 'rgba(245,166,35,0.4)' : 'transparent'}`,
                  borderRadius: 8,
                  color: mode === m ? '#F5A623' : 'var(--text-secondary)',
                  fontSize: 13, fontWeight: 600,
                  transition: 'all 0.2s',
                }}
              >{m === 'login' ? 'Sign In' : '⚡ Demo Login'}</button>
            ))}
          </div>

          {mode === 'login' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <button
                type="button"
                className="btn btn-secondary btn-lg"
                style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, background: '#fff', color: '#000' }}
                onClick={() => loginGoogle()}
                disabled={loading}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                {loading ? 'Signing in…' : 'Continue with Google'}
              </button>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <hr style={{ flex: 1, borderColor: 'var(--border-subtle)' }} />
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>or</span>
                <hr style={{ flex: 1, borderColor: 'var(--border-subtle)' }} />
              </div>

              <form onSubmit={handleLogin}>
                <label className="input-label">Email</label>
                <input
                  className="input"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  style={{ marginBottom: 14 }}
                  required
                />

                <label className="input-label">Password</label>
                <input
                  className="input"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  style={{ marginBottom: 20 }}
                  required
                />

                {error && (
                  <div style={{
                    background: 'rgba(239,68,68,0.1)',
                    border: '1px solid rgba(239,68,68,0.3)',
                    borderRadius: 8,
                    padding: '10px 14px',
                    fontSize: 13,
                    color: '#EF4444',
                    marginBottom: 16,
                  }}>{error}</div>
                )}

                <button
                  type="submit"
                  className="btn btn-primary btn-lg"
                  style={{ width: '100%' }}
                  disabled={loading}
                >{loading ? 'Signing in…' : 'Sign In with Email'}</button>
              </form>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>
                Click any account to instantly sign in:
              </p>
              {DEMO_ACCOUNTS.map(acc => (
                <button
                  key={acc.email}
                  onClick={() => handleLogin(undefined, acc.email, acc.password)}
                  disabled={loading}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 10,
                    padding: '12px 16px',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                    opacity: loading ? 0.6 : 1,
                  }}
                >
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>{acc.label}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{acc.email}</div>
                  </div>
                  <span className="pill pill-teal" style={{ fontSize: 10 }}>{acc.role}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-muted)', marginTop: 20 }}>
          No account? Demo credentials auto-create on first use.
        </p>
      </motion.div>
    </div>
  )
}
