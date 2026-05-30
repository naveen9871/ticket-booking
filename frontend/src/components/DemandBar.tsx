interface Props {
  pct: number
  label?: string
  color?: 'gold' | 'teal' | 'red'
}

const colorMap = {
  gold:  'linear-gradient(90deg, #F5A623, #EF4444)',
  teal:  'linear-gradient(90deg, #8FD6C8, #22D3EE)',
  red:   'linear-gradient(90deg, #EF4444, #F97316)',
}

export function DemandBar({ pct, label, color = 'teal' }: Props) {
  const clamped = Math.max(0, Math.min(100, pct))
  return (
    <div>
      {label && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'rgba(237,244,242,0.55)', marginBottom: 4 }}>
          <span>{label}</span>
          <span style={{ fontWeight: 700, color: clamped > 80 ? '#F5A623' : undefined }}>{clamped}%</span>
        </div>
      )}
      <div className="demand-bar-track">
        <div className="demand-bar-fill" style={{ width: `${clamped}%`, background: colorMap[color] }} />
      </div>
    </div>
  )
}
