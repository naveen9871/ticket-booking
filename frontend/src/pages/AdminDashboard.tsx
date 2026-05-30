import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis } from 'recharts'
import api from '../api'

const BOOKING_TREND = [
  { t: '6am', v: 120 }, { t: '8am', v: 340 }, { t: '10am', v: 890 },
  { t: '12pm', v: 2100 }, { t: '2pm', v: 1600 }, { t: '4pm', v: 1900 },
  { t: '6pm', v: 3200 }, { t: '8pm', v: 2800 }, { t: '10pm', v: 1400 },
]

const PENDING_THEATRES = [
  { id: 1, name: 'Galaxy Cinemas', city: 'Mysore', owner: 'Suresh R.', applied: '2 days ago' },
  { id: 2, name: 'Dream Screens', city: 'Hubli', owner: 'Priya M.', applied: '5 hours ago' },
  { id: 3, name: 'Royal IMAX', city: 'Mangalore', owner: 'Kiran D.', applied: '1 day ago' },
]

export default function AdminDashboard() {
  const [stats, setStats] = useState<Record<string, unknown> | null>(null)
  const [auditLog, setAuditLog] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([
      api.get('/autonomous/ops/dashboard'),
      api.get('/admin/audit-log'),
    ]).then(([statsRes, auditRes]) => {
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data)
      if (auditRes.status === 'fulfilled') setAuditLog(auditRes.value.data?.logs || [])
    }).finally(() => setLoading(false))
  }, [])

  const STAT_CARDS = [
    { label: 'Total Bookings', value: (stats as any)?.total_bookings ?? 14328, delta: '+12.4%', up: true, color: '#F5A623' },
    { label: 'Active Theatres', value: (stats as any)?.active_theatres ?? 89, delta: '+3', up: true, color: '#8FD6C8' },
    { label: 'Revenue (₹)', value: `${((stats as any)?.revenue_inr ?? 4820000).toLocaleString('en-IN')}`, delta: '+18.6%', up: true, color: '#22C55E' },
    { label: 'Seat Holds Active', value: (stats as any)?.active_holds ?? 412, delta: '-5.1%', up: false, color: '#F97316' },
    { label: 'Agent Sessions', value: (stats as any)?.agent_sessions ?? 2891, delta: '+34.2%', up: true, color: '#A855F7' },
    { label: 'Retry Success Rate', value: '73%', delta: '+2.1%', up: true, color: '#22C55E' },
  ]

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface-base)', padding: 24 }}>
      <div style={{ maxWidth: 1400, margin: '0 auto' }}>
        <div style={{ marginBottom: 28 }}>
          <p className="eyebrow">Super Admin</p>
          <h1 style={{ fontSize: 32, fontWeight: 800, fontFamily: "'Space Grotesk',sans-serif", marginTop: 4 }}>Platform Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: 6, fontSize: 14 }}>
            Real-time overview · Ticketly Autonomous Booking Platform
          </p>
        </div>

        {/* Stat cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: 14, marginBottom: 28 }}>
          {STAT_CARDS.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className="stat-card"
            >
              <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 10 }}>{s.label}</div>
              <div className="stat-value" style={{ color: s.color }}>{loading ? '—' : s.value}</div>
              <div className={`stat-delta ${s.up ? 'up' : 'down'}`} style={{ marginTop: 6 }}>
                {s.up ? '↑' : '↓'} {s.delta} this week
              </div>
            </motion.div>
          ))}
        </div>

        {/* Booking trend chart */}
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.5fr) minmax(0,1fr)', gap: 20, marginBottom: 24 }}>
          <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 20 }}>
            <div className="section-head">
              <div>
                <p className="eyebrow">Today's Booking Volume</p>
                <h3 style={{ fontSize: 20, marginTop: 4 }}>Reservation spike tracker</h3>
              </div>
              <span className="pill pill-success">
                <span className="live-dot" style={{ width: 5, height: 5 }} /> Live
              </span>
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={BOOKING_TREND}>
                <defs>
                  <linearGradient id="bookGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F5A623" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#F5A623" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="t" tick={{ fontSize: 10, fill: 'rgba(237,244,242,0.4)' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: '#141C28', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="v" stroke="#F5A623" strokeWidth={2} fill="url(#bookGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Pending theatre approvals */}
          <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 20 }}>
            <div className="section-head">
              <div>
                <p className="eyebrow">Approvals</p>
                <h3 style={{ fontSize: 20, marginTop: 4 }}>Pending theatres</h3>
              </div>
              <span className="pill pill-gold">{PENDING_THEATRES.length}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {PENDING_THEATRES.map(t => (
                <div key={t.id} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)',
                  borderRadius: 10, padding: '10px 14px',
                }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{t.name}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{t.city} · {t.owner} · {t.applied}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn btn-primary btn-sm">✓</button>
                    <button className="btn btn-danger btn-sm">✗</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Audit log */}
        <div style={{ background: 'var(--surface-02)', border: '1px solid var(--border-subtle)', borderRadius: 14, padding: 20 }}>
          <div className="section-head" style={{ marginBottom: 16 }}>
            <div>
              <p className="eyebrow">Audit Trail</p>
              <h3 style={{ fontSize: 20, marginTop: 4 }}>Recent platform actions</h3>
            </div>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th><th>Actor</th><th>Action</th><th>Resource</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              {(auditLog.length > 0 ? auditLog : [
                { id: 1, created_at: new Date().toISOString(), actor_user_id: 1, action: 'THEATRE_APPROVED', resource_type: 'Theatre', resource_id: '12', metadata_json: '{}' },
                { id: 2, created_at: new Date(Date.now() - 300000).toISOString(), actor_user_id: 2, action: 'USER_BANNED', resource_type: 'User', resource_id: '45', metadata_json: '{}' },
                { id: 3, created_at: new Date(Date.now() - 900000).toISOString(), actor_user_id: 1, action: 'PRICE_POLICY_UPDATED', resource_type: 'Policy', resource_id: 'global', metadata_json: '{}' },
                { id: 4, created_at: new Date(Date.now() - 1800000).toISOString(), actor_user_id: 3, action: 'BOOKING_CANCELLED', resource_type: 'Booking', resource_id: '889', metadata_json: '{}' },
              ]).slice(0, 8).map((log: any) => (
                <tr key={log.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text-muted)' }}>
                    {new Date(log.created_at).toLocaleTimeString()}
                  </td>
                  <td>User #{log.actor_user_id}</td>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 12 }}>{log.action}</td>
                  <td style={{ fontSize: 12 }}>{log.resource_type} #{log.resource_id}</td>
                  <td><span className="pill pill-success" style={{ fontSize: 9 }}>OK</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
