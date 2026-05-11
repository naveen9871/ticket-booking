import type { Listing, Seat, UserPreferences } from '../types'

export const mockPreferences: UserPreferences = {
  name: 'Arjun',
  city: 'Bengaluru',
  preferredSeat: 'recliner',
  travelClass: '2A',
  maxPrice: 2500,
  preferredProviders: ['PVR Orion', 'KSRTC', 'IRCTC'],
  dietary: ['veg'],
}

const now = Date.now()
const inHours = (h: number) => new Date(now + h * 60 * 60 * 1000).toISOString()

export const mockListings: Listing[] = [
  {
    id: 'm1',
    domain: 'movies',
    title: 'Kalki 2898 AD Part 2',
    subtitle: 'PVR Orion IMAX • 8:30 PM',
    city: 'Bengaluru',
    datetime: inHours(22),
    price: 560,
    score: 98,
    tags: ['IMAX', 'Recliner', 'Dolby'],
    amenities: ['Parking', 'Food Court'],
    reason: 'Most booked theatre + recliners available',
  },
  {
    id: 'm2',
    domain: 'movies',
    title: 'Pushpa 3',
    subtitle: 'INOX Vega • 6:00 PM',
    city: 'Bengaluru',
    datetime: inHours(18),
    price: 420,
    score: 93,
    tags: ['4DX', 'Action'],
    amenities: ['Dolby', 'Lounge'],
    reason: 'Middle rows available for group cluster',
  },
  {
    id: 'b1',
    domain: 'bus',
    title: 'Bangalore -> Mysore',
    subtitle: 'KSRTC Airavat Sleeper',
    city: 'Bengaluru',
    datetime: inHours(36),
    price: 899,
    score: 95,
    tags: ['Sleeper', 'Live Tracking'],
    amenities: ['WiFi', 'Charging', 'Water'],
    reason: 'Fits Sunday morning + preferred operator',
  },
  {
    id: 't1',
    domain: 'train',
    title: 'SBC -> MAS Shatabdi',
    subtitle: 'Coach C2 • WL4 (High confirmation)',
    city: 'Bengaluru',
    datetime: inHours(72),
    price: 1360,
    score: 91,
    tags: ['2A', 'Predictor High'],
    amenities: ['Meals', 'On-time'],
    reason: 'Strong historical confirmation for WL4',
  },
  {
    id: 'e1',
    domain: 'events',
    title: 'AR Rahman Live',
    subtitle: 'Palace Grounds • Gold Zone',
    city: 'Bengaluru',
    datetime: inHours(120),
    price: 2999,
    score: 89,
    tags: ['Live', 'Premium'],
    amenities: ['Food', 'Parking'],
    reason: 'Trending in your city this week',
  },
]

export const buildMockSeats = (): Seat[] => {
  const rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
  const seats: Seat[] = []
  rows.forEach((row, rowIndex) => {
    for (let i = 1; i <= 12; i += 1) {
      const id = `${row}${i}`
      const isTaken = Math.random() > 0.78
      const type = rowIndex > 4 ? 'recliner' : i <= 2 ? 'wheelchair' : 'standard'
      seats.push({
        id,
        row,
        number: i,
        type,
        status: isTaken ? 'taken' : 'available',
        price: type === 'recliner' ? 620 : 360,
      })
    }
  })
  return seats
}
