import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, ResponsiveContainer, XAxis, Tooltip } from 'recharts'
import api from '../api'

const MOCK_SCREENS = [
  { id: 1, name: 'Screen 1 – IMAX', capacity: 280, format: 'IMAX', status: 'Active' },
  { id: 2, name: 'Screen 2 – Dolby', capacity: 220, format: 'Dolby Atmos', status: 'Active' },
  { id: 3, name: 'Screen 3 – Standard', capacity: 180, format: '2D', status: 'Maintenance' },
]

const OCCUPANCY_DATA = [
  { day: 'Mon', pct: 62 }, { day: 'Tue', pct: 74 }, { day: 'Wed', pct: 58 },
  { day: 'Thu', pct: 81 }, { day: 'Fri', pct: 94 }, { day: 'Sat', pct: 99 }, { day: 'Sun', pct: 96 },
]

const UPCOMING_SHOWS = [
  { id: 1, movie: 'Coolie', time: 'Today 7:30 PM', format: 'IMAX', seats_sold: 245, capacity: 280, revenue: 137200 },
  { id: 2, movie: 'Pushpa 3', time: 'Today 10:00 PM', format: 'Dolby', seats_sold: 189, capacity: 220, revenue: 90720 },
  { id: 3, movie: 'Coolie', time: 'Tomorrow 12:00 PM', format: 'IMAX', seats_sold: 56, capacity: 280, revenue: 31360 },
  { id: 4, movie: 'KGF 3', time: 'Tomorrow 3:30 PM', format: '2D', seats_sold: 120, capacity: 180, revenue: 43200 },
]

export default function TheatreOwnerDashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'shows' | 'pricing' | 'screens'>('overview')

  const TABS = [
    { id: 'overview', label: '📊 Overview' },
    { id: 'shows', label: '🎬 Shows' },
    { id: 'screens', label: '🖥️ Screens' },
    { id: 'pricing', label: '💰 Pricing' },
  ] as const

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface-base)', padding: 24 }}>
      <div style={{ maxWidth: 1300, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <p className="eyebrow">Theatre Owner</p>
          <h1 style={{ fontSize: 30, fontWeight: 800, fontFamily: "'Space Grotesk',sans-serif", marginTop: 4 }}>
            PVR Orion IMAX — Bengaluru
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 6 }}>
            Rajajinagar · 3 screens · Approved ✓
          </p>
        </div>

        {/* Quick stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))', gap: 12, marginBottom: 24 }}>
          {[
            { label: "Today's Revenue", value: '₹2,27,920', delta: '+8.2%', color: '#F5A623' },
            { label: 'Seats Sold Today', value: '610', delta: '+14.1%', color: '#8FD6C8' },
            { label: 'Occupancy Rate', value: '86%', delta: '+3%', color: '#22C55E' },
            { label: 'Active Shows', value: '4', delta: '0', color: '#A855F7' },
          ].map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="stat-card"
            >
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>{s.label}</div>
              <div className="stat-value" style={{ color: s.color, fontSize: 28 }}>{s.value}</div>
              <div className="stat-delta up" style={{ marginTop: 4 }}>↑ {s.delta} vs yesterday</div>
            </motion.div>
          ))}
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: 4, width: 'fit-content' }}>
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              style={{
                padding: '8px 16px', borderRadius: 9,
                background: activeTab === t.id ? 'rgba(245,166,35,0.15)' : 'transparent',
                border: `1px solid ${activeTab === t.id ? 'rgba(245,166,35,0.4)' : 'transparent'}`,
                color: activeTab === t.id ? '#F5A623' : 'rgba(237,244,242,0.6)',
                fontSize: 13, fontWeight: 600, cursor: 'pointer', transition: 'all 0.15s',
              }}
            >{t.label}</button>
          ))}
        </div>

        {/* Tab content */}
        {activeTab === 'overview' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.4fr) minmax(0,1fr)', gap: 20 }}>
            {/* Occupancy chart */}
            <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 20 }}>
              <p className="eyebrow" style={{ marginBottom: 4 }}>This Week's Occupancy</p>
              <h3 style={{ fontSize: 20, marginBottom: 16 }}>Daily seat fill rate</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={OCCUPANCY_DATA} barSize={28}>
                  <XAxis dataKey="day" tick={{ fontSize: 11, fill: 'rgba(237,244,242,0.5)' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#141C28', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} formatter={(v: any) => [`${v}%`, 'Occupancy']} />
                  <Bar dataKey="pct" fill="#F5A623" radius={[5,5,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Recent shows */}
            <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 20 }}>
              <p className="eyebrow" style={{ marginBottom: 4 }}>Revenue Breakdown</p>
              <h3 style={{ fontSize: 20, marginBottom: 16 }}>Today's shows</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {UPCOMING_SHOWS.filter(s => s.time.startsWith('Today')).map(s => (
                  <div key={s.id} style={{
                    background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)',
                    borderRadius: 10, padding: '10px 14px',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{s.movie} · {s.time.replace('Today ', '')}</span>
                      <span className="pill pill-teal" style={{ fontSize: 9 }}>{s.format}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)' }}>
                      <span>{s.seats_sold}/{s.capacity} seats · {Math.round(s.seats_sold/s.capacity*100)}%</span>
                      <span style={{ color: '#22C55E', fontWeight: 600 }}>₹{s.revenue.toLocaleString('en-IN')}</span>
                    </div>
                    <div style={{ marginTop: 6, height: 4, borderRadius: 999, background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${Math.round(s.seats_sold/s.capacity*100)}%`, background: 'linear-gradient(90deg, #8FD6C8, #F5A623)', borderRadius: 999 }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'shows' && (
          <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 20 }}>
            <div className="section-head">
              <div>
                <p className="eyebrow">Show Manager</p>
                <h3 style={{ fontSize: 20, marginTop: 4 }}>All scheduled shows</h3>
              </div>
              <button className="btn btn-primary btn-sm">+ Add Show</button>
            </div>
            <table className="data-table">
              <thead>
                <tr><th>Movie</th><th>Date / Time</th><th>Format</th><th>Occupancy</th><th>Revenue</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {UPCOMING_SHOWS.map(s => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{s.movie}</td>
                    <td>{s.time}</td>
                    <td><span className="pill pill-teal" style={{ fontSize: 9 }}>{s.format}</span></td>
                    <td>
                      <span style={{ color: s.seats_sold/s.capacity > 0.85 ? '#22C55E' : '#F5A623', fontWeight: 600 }}>
                        {Math.round(s.seats_sold/s.capacity*100)}%
                      </span>
                    </td>
                    <td style={{ color: '#22C55E', fontWeight: 600 }}>₹{s.revenue.toLocaleString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button className="btn btn-ghost btn-sm">Edit</button>
                        <button className="btn btn-danger btn-sm">Cancel</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'screens' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(280px,1fr))', gap: 14 }}>
            {MOCK_SCREENS.map(sc => (
              <div key={sc.id} style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700 }}>{sc.name}</h3>
                  <span className={`pill ${sc.status === 'Active' ? 'pill-success' : 'pill-error'}`} style={{ fontSize: 10 }}>
                    {sc.status}
                  </span>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>
                  Capacity: {sc.capacity} seats
                </div>
                <span className="pill pill-teal" style={{ fontSize: 10, marginBottom: 14, display: 'inline-block' }}>{sc.format}</span>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn btn-secondary btn-sm" style={{ flex: 1 }}>Configure</button>
                  <button className="btn btn-primary btn-sm" style={{ flex: 1 }}>Seat Layout</button>
                </div>
              </div>
            ))}
            <div style={{
              background: 'rgba(255,255,255,0.02)', border: '2px dashed rgba(255,255,255,0.1)',
              borderRadius: 14, padding: 20, display: 'grid', placeItems: 'center',
              minHeight: 160, cursor: 'pointer',
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 32, marginBottom: 8, opacity: 0.5 }}>+</div>
                <div style={{ color: 'var(--text-muted)', fontSize: 14 }}>Add New Screen</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'pricing' && (
          <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 20 }}>
            <div className="section-head" style={{ marginBottom: 20 }}>
              <div>
                <p className="eyebrow">Pricing Config</p>
                <h3 style={{ fontSize: 20, marginTop: 4 }}>Seat tier pricing</h3>
              </div>
              <button className="btn btn-primary btn-sm">Save Changes</button>
            </div>
            <div style={{ display: 'grid', gap: 14 }}>
              {[
                { tier: 'Standard', base: 360, weekend: 420, peak: 480 },
                { tier: 'Premium', base: 480, weekend: 560, peak: 640 },
                { tier: 'Recliner', base: 620, weekend: 720, peak: 840 },
              ].map(t => (
                <div key={t.tier} style={{
                  display: 'grid', gridTemplateColumns: '140px 1fr 1fr 1fr',
                  gap: 14, alignItems: 'center',
                  background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)',
                  borderRadius: 10, padding: 14,
                }}>
                  <span style={{ fontWeight: 700, fontSize: 14 }}>{t.tier}</span>
                  {[['Base', t.base], ['Weekend', t.weekend], ['Peak/Surge', t.peak]].map(([label, val]) => (
                    <div key={label}>
                      <label className="input-label" style={{ marginBottom: 4 }}>{label}</label>
                      <input className="input" defaultValue={String(val)} style={{ padding: '8px 10px' }} />
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
