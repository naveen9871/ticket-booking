export type BookingDomain = 'movies' | 'bus' | 'train' | 'events'

export type SeatType = 'standard' | 'recliner' | 'couple' | 'wheelchair' | 'berth'

export type SeatStatus = 'available' | 'taken' | 'selected'

export interface Seat {
  id: string
  row: string
  number: number
  type: SeatType
  status: SeatStatus
  price: number
}

export interface Listing {
  id: string
  domain: BookingDomain
  title: string
  subtitle: string
  city: string
  datetime: string
  price: number
  score: number
  tags: string[]
  amenities: string[]
  reason: string
}

export interface UserPreferences {
  name: string
  city: string
  preferredSeat: SeatType
  travelClass: string
  maxPrice: number
  preferredProviders: string[]
  dietary: string[]
}

export interface ChatActionCard {
  kind: 'listing' | 'seatmap' | 'summary'
  listings?: Listing[]
  summary?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  cards?: ChatActionCard[]
  chips?: string[]
}
