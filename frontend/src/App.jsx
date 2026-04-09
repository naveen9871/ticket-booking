import React, { useEffect, useState } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import api, { setToken } from './api'
import ChatAssistant from './components/ChatAssistant'
import MovieCard from './components/MovieCard'

function Home({ selectedCity, setSelectedCity }) {
  const [movies, setMovies] = useState([])
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [cities, setCities] = useState([])
  const [cityMovieIds, setCityMovieIds] = useState(new Set())
  const [selectedMovie, setSelectedMovie] = useState(null)
  const [showtimes, setShowtimes] = useState([])

  useEffect(() => {
    api.get('/movies').then((res) => setMovies(res.data))
  }, [])

  useEffect(() => {
    api.get('/theatres').then((res) => {
      const uniqueCities = Array.from(new Set(res.data.map((t) => t.city))).sort()
      setCities(uniqueCities)
      if (!selectedCity && uniqueCities.length > 0) {
        setSelectedCity(uniqueCities[0])
      }
    })
  }, [selectedCity, setSelectedCity])

  useEffect(() => {
    if (!selectedCity) return
    api.get('/showtimes', { params: { city: selectedCity } }).then((res) => {
      const ids = new Set(res.data.map((s) => s.movie_id))
      setCityMovieIds(ids)
    })
  }, [selectedCity])

  const handleSearch = async () => {
    if (!query) return
    const res = await api.get('/search', { params: { query } })
    setResults(res.data)
  }

  const handleSelectMovie = async (movie) => {
    setSelectedMovie(movie)
    const res = await api.get('/showtimes', {
      params: { movie_id: movie.id, city: selectedCity || undefined }
    })
    setShowtimes(res.data)
  }

  const visibleMovies = selectedCity
    ? movies.filter((m) => cityMovieIds.has(m.id))
    : movies

  const filteredSearchMovies = results?.movies
    ? results.movies.filter((m) => !selectedCity || cityMovieIds.has(m.id))
    : []

  return (
    <div className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">Ticketly • Smart Booking</p>
          <h1>Book your next experience in a single conversation.</h1>
          <p className="subtitle">
            Discover movies, see real-time pricing, and let the assistant pick the best seats.
          </p>
          <div className="search">
            <input
              placeholder="Search movies, theatres, cities"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button onClick={handleSearch}>Search</button>
          </div>
          <div className="location-row">
            <label>Location</label>
            <select value={selectedCity} onChange={(e) => setSelectedCity(e.target.value)}>
              <option value="">All Cities</option>
              {cities.map((city) => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>
          {results && (
            <div className="search-results">
              <h3>Search Results</h3>
              <div className="grid">
                {filteredSearchMovies.map((movie) => (
                  <MovieCard key={movie.id} movie={movie} compact onSelect={handleSelectMovie} />
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="hero-panel">
          <div className="hero-card">
            <h3>Tonight's Picks</h3>
            <p>Handpicked showtimes based on trending demand.</p>
            <ul>
              {visibleMovies.slice(0, 3).map((movie) => (
                <li key={movie.id}>
                  <span>{movie.title}</span>
                  <span className="pill">{movie.genre}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="hero-card glow">
            <h3>Auto Seat Selection</h3>
            <p>AI chooses the best contiguous seats near center.</p>
            <button className="ghost">Try Assistant</button>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <h2>Now Showing</h2>
          <span className="muted">{selectedCity ? `In ${selectedCity}` : 'Curated for your city'}</span>
        </div>
        <div className="grid">
          {visibleMovies.map((movie) => (
            <MovieCard key={movie.id} movie={movie} onSelect={handleSelectMovie} />
          ))}
        </div>
      </section>

      {selectedMovie && (
        <section className="section">
          <div className="section-header">
            <h2>Showtimes for {selectedMovie.title}</h2>
            <span className="muted">{selectedCity ? `In ${selectedCity}` : 'All cities'}</span>
          </div>
          <div className="showtime-list">
            {showtimes.length === 0 && <p className="muted">No showtimes available.</p>}
            {showtimes.map((s) => (
              <div key={s.id} className="showtime-card">
                <div>
                  <strong>{new Date(s.start_time).toLocaleString()}</strong>
                  <div className="muted">{s.theatre_name} • {s.format}</div>
                </div>
                <div className="price">₹{Math.round(s.base_price)}</div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

import Login from './pages/Login'
import AdminDashboard from './pages/AdminDashboard'

function App() {
  const [user, setUser] = useState(null)
  const token = user?.access_token
  const [selectedCity, setSelectedCity] = useState('')

  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">Ticketly</Link>
        <nav>
          <Link to="/">Explore</Link>
          <Link to="/admin">Admin</Link>
          {user ? (
            <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{user.user.full_name || user.user.phone}</span>
          ) : (
            <Link to="/login"><button className="primary">Login</button></Link>
          )}
        </nav>
      </header>
      <main className="layout">
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <Routes>
            <Route path="/" element={<Home selectedCity={selectedCity} setSelectedCity={setSelectedCity} />} />
            <Route path="/login" element={<Login onLogin={(data) => { setUser(data); window.location.hash = '' }} />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Routes>
        </div>
        <aside id="assistant" className="assistant">
          <ChatAssistant token={token} city={selectedCity} />
        </aside>
      </main>
    </div>
  )
}

export default App
