import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { buildMockSeats, mockPreferences } from '../data/mockData'
import type { Listing, Seat, UserPreferences } from '../types'

interface BookingState {
  preferences: UserPreferences
  selectedDomain: 'movies' | 'bus' | 'train' | 'events'
  selectedListing: Listing | null
  seats: Seat[]
  selectedSeats: string[]
  setDomain: (domain: BookingState['selectedDomain']) => void
  updatePreferences: (prefs: Partial<UserPreferences>) => void
  chooseListing: (listing: Listing) => void
  toggleSeat: (seatId: string) => void
  resetSeats: () => void
}

export const useBookingStore = create<BookingState>()(
  persist(
    (set, get) => ({
      preferences: mockPreferences,
      selectedDomain: 'movies',
      selectedListing: null,
      seats: buildMockSeats(),
      selectedSeats: [],
      setDomain: (domain) => set({ selectedDomain: domain }),
      updatePreferences: (prefs) => set({ preferences: { ...get().preferences, ...prefs } }),
      chooseListing: (listing) => set({ selectedListing: listing, seats: buildMockSeats(), selectedSeats: [] }),
      toggleSeat: (seatId) =>
        set((state) => {
          const seat = state.seats.find((s) => s.id === seatId)
          if (!seat || seat.status === 'taken') return state
          const has = state.selectedSeats.includes(seatId)
          return { selectedSeats: has ? state.selectedSeats.filter((id) => id !== seatId) : [...state.selectedSeats, seatId] }
        }),
      resetSeats: () => set({ seats: buildMockSeats(), selectedSeats: [] }),
    }),
    { name: 'ticket-agentic-store-v1' },
  ),
)
