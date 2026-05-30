import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
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
  const [mobileOpen, setMobileOpen] = useState(false)

  const links = [
    { to: '/', label: 'Discover' },
    { to: '/owner', label: 'For theatres', show: true },
    { to: '/admin', label: 'Admin', show: user?.is_admin },
  ]

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
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 34, height: 34, borderRadius: '50%',
              background: 'linear-gradient(135deg, #F5A623, #EF4444)',
              display: 'grid', placeItems: 'center',
              fontSize: 13, fontWeight: 700, color: '#fff',
              cursor: 'pointer',
            }}>
              {(user?.full_name || user?.email || 'U')[0].toUpperCase()}
            </div>
            <button
              onClick={() => { logout(); navigate('/login') }}
              className="btn btn-ghost btn-sm"
              style={{ fontSize: 13 }}
            >Sign out</button>
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
