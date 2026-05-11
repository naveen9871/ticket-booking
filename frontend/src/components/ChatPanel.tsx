import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { orchestrateAgent } from '../agents/orchestrator'
import { useBookingStore } from '../store/useBookingStore'
import type { ChatMessage, Listing } from '../types'

const starters = [
  'Book 2 seats for Kalki tomorrow night in Bengaluru, recliner please',
  'Need a bus from Bangalore to Mysore this Sunday morning, sleeper',
  'Find train from Bangalore to Chennai next week, best 2A option',
]

interface Props {
  mobileOpen: boolean
  setMobileOpen: (open: boolean) => void
}

export const ChatPanel = ({ mobileOpen, setMobileOpen }: Props) => {
  const { preferences, chooseListing } = useBookingStore()
  const [input, setInput] = useState('')
  const [typing, setTyping] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: crypto.randomUUID(),
      role: 'assistant',
      text: `Good evening, ${preferences.name}. Kalki 2898 AD Part 2 releases Friday - want me to grab your usual recliner seats at PVR Orion?`,
      chips: ['Yes, 2 seats', 'Show buses', 'Set price alert'],
    },
  ])

  const send = async (text: string) => {
    if (!text.trim()) return
    setMessages((x) => [...x, { id: crypto.randomUUID(), role: 'user', text }])
    setInput('')
    setTyping(true)
    try {
      const reply = await orchestrateAgent(text, preferences)
      setMessages((x) => [...x, reply])
    } finally {
      setTyping(false)
    }
  }

  const chooseFromCard = (listing: Listing) => {
    chooseListing(listing)
    setMessages((x) => [
      ...x,
      {
        id: crypto.randomUUID(),
        role: 'assistant',
        text: `Booked flow prepared for ${listing.title}. I auto-selected your preferred seats. Confirm in the main pane.`,
        chips: ['Confirm booking', 'Change seats', 'Set alert'],
      },
    ])
  }

  return (
    <div className={`chat-shell ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="chat-head">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-amber-300">Concierge Agent</p>
          <h2 className="font-display text-2xl text-white">Always-on booking chat</h2>
        </div>
        <button className="md:hidden rounded-full border border-white/20 px-3 py-1 text-xs text-white/80" onClick={() => setMobileOpen(false)}>
          Close
        </button>
      </div>

      <div className="chat-body">
        {messages.map((m) => (
          <motion.div key={m.id} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className={`bubble ${m.role}`}>
            <p>{m.text}</p>
            {m.cards?.map((card, idx) => (
              <div key={`${m.id}-${idx}`} className="mt-3 space-y-2">
                {card.listings?.map((item) => (
                  <div key={item.id} className="rounded-xl border border-white/10 bg-white/5 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h4 className="font-semibold text-white">{item.title}</h4>
                        <p className="text-xs text-white/60">{item.subtitle}</p>
                        <p className="mt-1 text-xs text-amber-200">{item.reason}</p>
                      </div>
                      <button className="rounded-lg bg-[#F5A623] px-2 py-1 text-xs font-semibold text-black" onClick={() => chooseFromCard(item)}>
                        Book This
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ))}
            <div className="mt-2 flex flex-wrap gap-2">
              {m.chips?.map((chip) => (
                <button key={chip} className="rounded-full border border-white/15 px-2 py-1 text-[11px] text-white/70" onClick={() => send(chip)}>
                  {chip}
                </button>
              ))}
            </div>
          </motion.div>
        ))}
        <AnimatePresence>
          {typing && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="bubble assistant">
              <div className="flex gap-1">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="space-y-2">
        <div className="flex flex-wrap gap-2">
          {starters.map((s) => (
            <button key={s} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/70" onClick={() => send(s)}>
              {s}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            aria-label="Chat input"
            className="w-full rounded-xl border border-white/15 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-amber-400"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send(input)}
            placeholder="Ask for movies, buses, trains, events..."
          />
          <button className="rounded-xl bg-[#F5A623] px-3 py-2 text-sm font-semibold text-black" onClick={() => send(input)}>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
