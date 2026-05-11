import { useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useVirtualizer } from '@tanstack/react-virtual'
import { motion } from 'framer-motion'
import { mockListings } from './data/mockData'
import { useBookingStore } from './store/useBookingStore'
import { ChatPanel } from './components/ChatPanel'
import { SeatMapSvg } from './components/SeatMapSvg'
import type { Listing } from './types'

const categories = [
  { id: 'movies', label: 'Movies' },
  { id: 'bus', label: 'Bus' },
  { id: 'train', label: 'Train' },
  { id: 'events', label: 'Events' },
] as const

const fetchListings = async () => {
  await new Promise((r) => setTimeout(r, 280))
  return mockListings
}

function App() {
  const { preferences, selectedDomain, setDomain, selectedListing, chooseListing, seats, selectedSeats, toggleSeat } = useBookingStore()
  const [mobileChatOpen, setMobileChatOpen] = useState(false)
  const { data = [] } = useQuery({ queryKey: ['listings'], queryFn: fetchListings })
  const listRef = useRef<HTMLDivElement | null>(null)

  const filtered = useMemo(() => data.filter((x) => x.domain === selectedDomain), [data, selectedDomain])
  const rowVirtualizer = useVirtualizer({
    count: filtered.length,
    getScrollElement: () => listRef.current,
    estimateSize: () => 110,
  })

  const confirmText = selectedListing
    ? `Ready to confirm ${selectedSeats.length} seat(s) for ${selectedListing.title} at Rs ${selectedSeats.length * selectedListing.price}.`
    : 'Select a card from chat or dashboard to continue booking.'

  return (
    <div className="min-h-screen bg-[#0D0F14] text-[#F5F7FA]">
      <div className="mx-auto flex max-w-[1600px] gap-0">
        <aside className={`left-chat ${mobileChatOpen ? 'open' : ''}`}>
          <ChatPanel mobileOpen={mobileChatOpen} setMobileOpen={setMobileChatOpen} />
        </aside>

        <main className="flex-1 px-4 py-5 md:px-8">
          <header className="mb-6 flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 p-4">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-amber-300">Ticket Operating System</p>
              <h1 className="font-display text-4xl leading-tight md:text-5xl">
                Good evening, {preferences.name}. Here&apos;s what&apos;s trending near {preferences.city} tonight.
              </h1>
            </div>
            <button className="rounded-full border border-white/20 px-4 py-2 text-sm md:hidden" onClick={() => setMobileChatOpen(true)}>
              Chat with Agent
            </button>
          </header>

          <section className="mb-6 grid gap-3 md:grid-cols-5">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setDomain(cat.id)}
                className={`rounded-full border px-4 py-2 text-sm transition ${selectedDomain === cat.id ? 'border-amber-400 bg-amber-400/15 text-amber-200' : 'border-white/15 bg-white/5 text-white/75'}`}
              >
                {cat.label}
              </button>
            ))}
          </section>

          <section className="mb-6 grid gap-4 lg:grid-cols-3">
            {filtered.map((item) => (
              <motion.button
                key={item.id}
                whileHover={{ y: -8, rotateX: 4, rotateY: -4 }}
                transition={{ type: 'spring', stiffness: 280, damping: 24 }}
                onClick={() => chooseListing(item)}
                className="text-left rounded-2xl border border-white/10 bg-[#121721] p-4 shadow-[0_12px_40px_rgba(0,0,0,.35)]"
              >
                <p className="text-xs text-amber-300">{item.domain.toUpperCase()}</p>
                <h3 className="mt-1 font-display text-2xl">{item.title}</h3>
                <p className="text-sm text-white/65">{item.subtitle}</p>
                <p className="mt-3 text-xs text-white/75">{item.reason}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {item.tags.map((t) => (
                    <span key={t} className="rounded-full border border-white/20 px-2 py-1 text-[11px] text-white/70">{t}</span>
                  ))}
                </div>
              </motion.button>
            ))}
          </section>

          <section className="mb-6 rounded-2xl border border-white/10 bg-[#10151E] p-4">
            <h2 className="font-display text-3xl">Seat / Berth Selection</h2>
            <p className="mb-3 text-sm text-white/60">{selectedListing?.title || 'Pick a listing to open interactive map'}</p>
            <SeatMapSvg seats={seats} selectedSeats={selectedSeats} onToggle={toggleSeat} />
          </section>

          <section className="rounded-2xl border border-white/10 bg-[#10151E] p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-display text-2xl">Ranked Results (Virtualized)</h2>
              <span className="text-xs text-white/55">{filtered.length} matches</span>
            </div>
            <div ref={listRef} id="listing-scroll" className="h-72 overflow-auto rounded-xl border border-white/10 bg-black/20">
              <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, position: 'relative' }}>
                {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                  const item: Listing = filtered[virtualRow.index]
                  return (
                    <div
                      key={item.id}
                      className="absolute left-0 top-0 w-full border-b border-white/5 p-3"
                      style={{ transform: `translateY(${virtualRow.start}px)` }}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold">{item.title}</p>
                          <p className="text-xs text-white/55">{item.subtitle}</p>
                        </div>
                        <button className="rounded-lg border border-amber-400/50 bg-amber-300/15 px-3 py-1 text-xs" onClick={() => chooseListing(item)}>
                          Book This
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </section>

          <footer className="sticky bottom-3 mt-5 rounded-2xl border border-white/10 bg-[#151B26]/95 p-3 backdrop-blur">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-white/80">{confirmText}</p>
              <button className="rounded-xl bg-[#F5A623] px-4 py-2 text-sm font-semibold text-black">Confirm & Pay</button>
            </div>
          </footer>
        </main>
      </div>
    </div>
  )
}

export default App
