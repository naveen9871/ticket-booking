export interface SeatData {
  id: string
  row: string
  number: number
  type: 'standard' | 'recliner' | 'wheelchair' | 'premium'
  status: 'available' | 'booked' | 'held' | 'held_by_you'
  price: number
  isAiPick?: boolean
}

interface Props {
  seats: SeatData[]
  selectedSeats: string[]
  onToggle: (seatId: string) => void
  showLegend?: boolean
}

function groupByRow(seats: SeatData[]) {
  const map = new Map<string, SeatData[]>()
  seats.forEach(s => {
    if (!map.has(s.row)) map.set(s.row, [])
    map.get(s.row)!.push(s)
  })
  return map
}

export function SeatMap({ seats, selectedSeats, onToggle, showLegend = true }: Props) {
  const rows = groupByRow(seats)
  const maxCols = Math.max(...Array.from(rows.values()).map(r => r.length))
  const midCol = Math.ceil(maxCols / 2)

  return (
    <div>
      {/* Screen indicator */}
      <div style={{
        textAlign: 'center', marginBottom: 20,
        padding: '8px 0',
        background: 'linear-gradient(to bottom, rgba(143,214,200,0.18), transparent)',
        borderTop: '3px solid rgba(143,214,200,0.5)',
        borderRadius: '12px 12px 0 0',
        fontSize: 11, fontWeight: 600, letterSpacing: '0.15em', textTransform: 'uppercase',
        color: 'rgba(143,214,200,0.7)',
      }}>
        ◀ SCREEN THIS WAY ▶
      </div>

      <div className="seat-grid">
        {Array.from(rows.entries()).map(([row, rowSeats]) => (
          <div key={row} className="seat-row">
            <div className="row-label">{row}</div>
            {rowSeats.map((seat, idx) => {
              const isSelected = selectedSeats.includes(seat.id)
              const isBooked = seat.status === 'booked'
              const isHeld = seat.status === 'held'
              const isYours = seat.status === 'held_by_you'
              const isAiPick = seat.isAiPick && !isSelected

              // Insert aisle gap at middle
              const needsAisle = idx === midCol - 1

              const cls = [
                'seat-btn',
                isSelected || isYours ? 'selected' : '',
                isBooked ? 'booked' : '',
                isHeld ? 'held' : '',
                isAiPick ? 'ai-pick' : '',
              ].filter(Boolean).join(' ')

              return (
                <span key={seat.id} style={{ display: 'contents' }}>
                  <button
                    className={cls}
                    disabled={isBooked || isHeld}
                    onClick={() => onToggle(seat.id)}
                    title={`${seat.id} · ${seat.type} · ₹${seat.price}`}
                  >
                    {seat.number}
                  </button>
                  {needsAisle && <span className="aisle-gap" />}
                </span>
              )
            })}
          </div>
        ))}
      </div>

      {showLegend && (
        <div className="seat-legend">
          {[
            { cls: '', label: 'Available', bg: 'rgba(143,214,200,0.12)', border: 'rgba(143,214,200,0.25)' },
            { cls: 'selected', label: 'Selected', bg: '#F5A623', border: '#F5A623' },
            { cls: 'ai-pick', label: 'AI Recommended', bg: 'rgba(59,130,246,0.22)', border: 'rgba(59,130,246,0.5)' },
            { cls: 'held', label: 'On Hold', bg: 'rgba(245,166,35,0.12)', border: 'rgba(245,166,35,0.25)' },
            { cls: 'booked', label: 'Booked', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.22)' },
          ].map(item => (
            <div key={item.label} className="legend-item">
              <div className="legend-dot" style={{ background: item.bg, borderColor: item.border }} />
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
