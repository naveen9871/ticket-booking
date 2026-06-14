import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'

const CITIES = ['Bengaluru', 'Hyderabad', 'Chennai', 'Mumbai', 'Delhi', 'Pune', 'Kolkata']

interface Props {
  city: string
  onCityChange: (c: string) => void
}

export function NavBar({ city, onCityChange }: Props) {
  const { user, logout, isLoggedIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [cityOpen, setCityOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const profileRef = useRef<HTMLDivElement>(null)

  // Close profile dropdown when clicking outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const links = [
    { to: '/', label: 'Discover' },
    { to: '/owner', label: 'For theatres', show: true },
    { to: '/admin', label: 'Admin', show: user?.is_admin },
  ]

  const displayName = user?.full_name || user?.email || 'User'
  const avatarLetter = displayName[0].toUpperCase()

  return (
    <nav
      style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(9,12,16,0.88)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}
    >
      <div style={{ maxWidth: 1440, margin: '0 auto', padding: '0 20px', display: 'flex', alignItems: 'center', height: 60, gap: 20 }}>
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none', flexShrink: 0 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #F5A623, #EF4444)',
            display: 'grid', placeItems: 'center',
            fontSize: 16, fontWeight: 900, color: '#fff',
          }}>T</div>
          <span style={{ fontSize: 18, fontWeight: 800, fontFamily: "'Space Grotesk',sans-serif", color: '#EDF4F2' }}>
            Ticketly
          </span>
        </Link>

        {/* Nav links */}
        <div style={{ display: 'flex', gap: 4, flex: 1 }}>
          {links.filter(l => l.show !== false).map(l => (
            <Link
              key={l.to}
              to={l.to}
              style={{
                padding: '6px 14px',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 500,
                color: location.pathname === l.to ? '#F5A623' : 'rgba(237,244,242,0.7)',
                background: location.pathname === l.to ? 'rgba(245,166,35,0.1)' : 'transparent',
                textDecoration: 'none',
                transition: 'all 0.15s',
              }}
            >{l.label}</Link>
          ))}
        </div>

        {/* City picker */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setCityOpen(p => !p)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: 8,
              padding: '6px 12px',
              color: 'rgba(237,244,242,0.85)',
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            📍 {city} <span style={{ opacity: 0.5 }}>▾</span>
          </button>
          {cityOpen && (
            <div style={{
              position: 'absolute', top: '110%', right: 0,
              background: '#141C28',
              border: '1px solid rgba(255,255,255,0.12)',
              borderRadius: 10,
              padding: 6,
              minWidth: 150,
              zIndex: 200,
              boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
            }}>
              {CITIES.map(c => (
                <button
                  key={c}
                  onClick={() => { onCityChange(c); setCityOpen(false) }}
                  style={{
                    display: 'block', width: '100%', textAlign: 'left',
                    padding: '8px 12px', borderRadius: 7,
                    background: c === city ? 'rgba(245,166,35,0.12)' : 'transparent',
                    color: c === city ? '#F5A623' : 'rgba(237,244,242,0.8)',
                    fontSize: 13,
                    border: 'none',
                    fontWeight: c === city ? 600 : 400,
                    transition: 'all 0.1s',
                  }}
                >{c}</button>
              ))}
            </div>
          )}
        </div>

        {/* Auth */}
        {isLoggedIn ? (
          <div ref={profileRef} style={{ position: 'relative' }}>
            <button
              onClick={() => setProfileOpen(p => !p)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: 24,
                padding: '4px 12px 4px 4px',
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              <div style={{
                width: 30, height: 30, borderRadius: '50%',
                background: 'linear-gradient(135deg, #F5A623, #EF4444)',
                display: 'grid', placeItems: 'center',
                fontSize: 13, fontWeight: 700, color: '#fff',
                flexShrink: 0,
              }}>
                {avatarLetter}
              </div>
              <span style={{ fontSize: 13, fontWeight: 500, color: 'rgba(237,244,242,0.85)', maxWidth: 100, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user?.full_name || user?.email?.split('@')[0]}
              </span>
              <span style={{ opacity: 0.4, fontSize: 10 }}>▾</span>
            </button>

            {profileOpen && (
              <div style={{
                position: 'absolute', top: 'calc(100% + 8px)', right: 0,
                background: '#141C28',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: 12,
                padding: 8,
                minWidth: 220,
                zIndex: 200,
                boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
              }}>
                {/* User info */}
                <div style={{ padding: '10px 12px 12px', borderBottom: '1px solid rgba(255,255,255,0.08)', marginBottom: 6 }}>
                  <div style={{ fontWeight: 700, fontSize: 14, color: '#EDF4F2' }}>{user?.full_name || 'User'}</div>
                  <div style={{ fontSize: 12, color: 'rgba(237,244,242,0.45)', marginTop: 2 }}>{user?.email}</div>
                  {user?.is_admin && (
                    <span style={{ display: 'inline-block', marginTop: 6, fontSize: 10, padding: '2px 8px', borderRadius: 99, background: 'rgba(245,166,35,0.15)', color: '#F5A623', fontWeight: 600 }}>
                      Admin
                    </span>
                  )}
                </div>

                {/* Menu items */}
                {[
                  { label: '🎟️ My Bookings', action: () => { navigate('/my-bookings'); setProfileOpen(false) } },
                  { label: '⚙️ Settings', action: () => setProfileOpen(false) },
                ].map(item => (
                  <button
                    key={item.label}
                    onClick={item.action}
                    style={{
                      display: 'block', width: '100%', textAlign: 'left',
                      padding: '9px 12px', borderRadius: 8,
                      background: 'transparent',
                      color: 'rgba(237,244,242,0.8)',
                      fontSize: 13, border: 'none', cursor: 'pointer',
                      transition: 'background 0.1s',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.05)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >{item.label}</button>
                ))}

                <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', marginTop: 6, paddingTop: 6 }}>
                  <button
                    onClick={() => { logout(); navigate('/login'); setProfileOpen(false) }}
                    style={{
                      display: 'block', width: '100%', textAlign: 'left',
                      padding: '9px 12px', borderRadius: 8,
                      background: 'transparent',
                      color: '#EF4444',
                      fontSize: 13, border: 'none', cursor: 'pointer',
                      transition: 'background 0.1s',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'rgba(239,68,68,0.08)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >🚪 Sign out</button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={() => navigate('/login')} className="btn btn-secondary btn-sm">Login</button>
            <button onClick={() => navigate('/login')} className="btn btn-primary btn-sm">Sign up</button>
          </div>
        )}
      </div>
    </nav>
  )
}
