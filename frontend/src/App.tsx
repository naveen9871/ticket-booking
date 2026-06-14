import { Suspense, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { NavBar } from './components/NavBar'
import { useAuth } from './hooks/useAuth'
import './styles.css'

// Lazy pages
import HomePage from './pages/HomePage'
import MovieDetailPage from './pages/MovieDetailPage'
import SeatMapPage from './pages/SeatMapPage'
import CheckoutPage from './pages/CheckoutPage'
import TicketPage from './pages/TicketPage'
import LoginPage from './pages/LoginPage'
import AdminDashboard from './pages/AdminDashboard'
import TheatreOwnerDashboard from './pages/TheatreOwnerDashboard'
import MyBookingsPage from './pages/MyBookingsPage'

function PageLoader() {
  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'var(--surface-base)' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: 48, height: 48,
          border: '3px solid rgba(245,166,35,0.3)',
          borderTopColor: '#F5A623',
          borderRadius: '50%',
          animation: 'spin-slow 1s linear infinite',
          margin: '0 auto 14px',
        }} />
        <p style={{ color: 'rgba(237,244,242,0.45)', fontSize: 14 }}>Loading…</p>
      </div>
    </div>
  )
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isLoggedIn } = useAuth()
  if (!isLoggedIn) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AppRoutes() {
  const [city, setCity] = useState('Bengaluru')

  return (
    <>
      <NavBar city={city} onCityChange={setCity} />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<HomePage city={city} />} />
          <Route path="/movie/:id" element={<MovieDetailPage />} />
          <Route path="/seats/:showtimeId" element={<SeatMapPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/ticket/:bookingId" element={<TicketPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/my-bookings" element={<RequireAuth><MyBookingsPage /></RequireAuth>} />
          <Route path="/admin" element={<RequireAuth><AdminDashboard /></RequireAuth>} />
          <Route path="/owner" element={<RequireAuth><TheatreOwnerDashboard /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
