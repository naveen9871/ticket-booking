import { motion } from 'framer-motion'
import type { Seat } from '../types'

interface Props {
  seats: Seat[]
  selectedSeats: string[]
  onToggle: (id: string) => void
}

const seatFill = (seat: Seat, selected: boolean) => {
  if (seat.status === 'taken') return '#1D232D'
  if (selected) return '#F5A623'
  return '#F4F5F7'
}

export const SeatMapSvg = ({ seats, selectedSeats, onToggle }: Props) => (
  <div className="rounded-2xl border border-white/10 bg-[#0F141D] p-4">
    <div className="mb-3 text-xs uppercase tracking-[0.2em] text-white/55">Screen</div>
    <svg viewBox="0 0 640 320" className="h-72 w-full">
      <path d="M70 34 Q320 -6 570 34" stroke="#F5A623" strokeOpacity="0.5" fill="none" strokeWidth="3" />
      {seats.map((seat, idx) => {
        const rowIndex = seat.row.charCodeAt(0) - 65
        const x = 50 + ((idx % 12) * 46)
        const y = 72 + rowIndex * 30
        const selected = selectedSeats.includes(seat.id)
        return (
          <motion.g
            key={seat.id}
            initial={false}
            animate={{ scale: selected ? 1.07 : 1 }}
            transition={{ type: 'spring', stiffness: 400, damping: 26 }}
            onClick={() => onToggle(seat.id)}
            className={seat.status === 'taken' ? 'cursor-not-allowed' : 'cursor-pointer'}
          >
            <rect x={x} y={y} width={28} height={20} rx={4} fill={seatFill(seat, selected)} stroke={selected ? '#FFE7B3' : '#2A3240'} />
          </motion.g>
        )
      })}
    </svg>
  </div>
)
