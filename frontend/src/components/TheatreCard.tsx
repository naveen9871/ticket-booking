import { DemandBar } from './DemandBar'

export interface TheatreCardData {
  id: number | string
  name: string
  city: string
  address: string
  supported_formats?: string[]
  amenities?: string[]
  base_price?: number
  score?: number
  occupancy?: number
  rank?: number
}

interface Props {
  theatre: TheatreCardData
  selected?: boolean
  onClick?: () => void
}

export function TheatreCard({ theatre, selected, onClick }: Props) {
  const formats = theatre.supported_formats ?? ['Standard']
  const occ = theatre.occupancy ?? Math.floor(30 + Math.random() * 60)

  return (
    <button
      onClick={onClick}
      style={{
        width: '100%', textAlign: 'left', background: 'none',
        border: `1px solid ${selected ? 'rgba(245,166,35,0.55)' : 'rgba(255,255,255,0.09)'}`,
        borderRadius: 12,
        padding: 14,
        transition: 'all 0.2s',
        cursor: 'pointer',
        backgroundColor: selected ? 'rgba(245,166,35,0.07)' : 'rgba(255,255,255,0.03)',
        display: 'grid',
        gridTemplateColumns: theatre.rank ? '32px 1fr auto' : '1fr auto',
        gap: 12,
        alignItems: 'center',
      } as React.CSSProperties}
    >
      {theatre.rank && (
        <div style={{
          width: 30, height: 30, borderRadius: '50%',
          background: 'rgba(143,214,200,0.14)',
          color: '#8FD6C8',
          display: 'grid', placeItems: 'center',
          fontSize: 13, fontWeight: 800,
          flexShrink: 0,
        }}>{theatre.rank}</div>
      )}

      <div style={{ minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: '#EDF4F2', marginBottom: 2 }} className="truncate">
          {theatre.name}
        </div>
        <div style={{ fontSize: 12, color: 'rgba(237,244,242,0.5)', marginBottom: 8 }} className="truncate">
          {theatre.city} · {theatre.address.slice(0, 40)}
        </div>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 8 }}>
          {formats.slice(0, 4).map(f => (
            <span key={f} className="pill pill-teal" style={{ fontSize: 9 }}>{f}</span>
          ))}
        </div>

        <DemandBar pct={occ} label={`${occ}% occupied`} />
      </div>

      {theatre.base_price && (
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ fontSize: 16, fontWeight: 800, color: '#F5A623' }}>₹{theatre.base_price}</div>
          {theatre.score && <div style={{ fontSize: 11, color: 'rgba(237,244,242,0.45)', marginTop: 2 }}>{theatre.score}% fit</div>}
        </div>
      )}
    </button>
  )
}
