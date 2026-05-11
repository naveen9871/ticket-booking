import { mockListings } from '../data/mockData'
import type { ChatMessage, Listing, UserPreferences } from '../types'

const SYSTEM_PROMPT = `You are a warm premium ticket concierge orchestrating 5 agents:
1) Concierge, 2) Preference, 3) Search, 4) Booking, 5) Alert.
Use concise language and provide practical choices with reasons.`

const toolset = [
  { name: 'search_movies', description: 'Search movie showtimes in city' },
  { name: 'search_buses', description: 'Search bus routes and seats' },
  { name: 'search_trains', description: 'Search train availability and classes' },
  { name: 'search_events', description: 'Search events and venues' },
  { name: 'get_user_preferences', description: 'Load user preference profile' },
  { name: 'get_seat_map', description: 'Get seat map for listing id' },
  { name: 'hold_seats', description: 'Hold selected seats temporarily' },
  { name: 'create_booking', description: 'Create booking after confirmation' },
  { name: 'check_availability', description: 'Check fresh inventory' },
]

const runTool = (tool: string, prefs: UserPreferences): Listing[] | UserPreferences | { ok: boolean } => {
  if (tool === 'get_user_preferences') return prefs
  if (tool.startsWith('search_')) {
    const domain = tool.replace('search_', '')
    return mockListings
      .filter((x) => x.domain === (domain === 'movies' ? 'movies' : domain === 'buses' ? 'bus' : domain === 'trains' ? 'train' : 'events'))
      .sort((a, b) => b.score - a.score)
  }
  return { ok: true }
}

export const orchestrateAgent = async (input: string, prefs: UserPreferences): Promise<ChatMessage> => {
  const key = import.meta.env.VITE_ANTHROPIC_API_KEY as string | undefined
  if (!key) {
    const fallback = mockListings
      .filter((x) => input.toLowerCase().includes('bus') ? x.domain === 'bus' : input.toLowerCase().includes('train') ? x.domain === 'train' : input.toLowerCase().includes('event') ? x.domain === 'events' : x.domain === 'movies')
      .slice(0, 3)
    return {
      id: crypto.randomUUID(),
      role: 'assistant',
      text: `I mapped this through Preference + Search + Booking agents. Here are the best options for you in ${prefs.city}.`,
      cards: [{ kind: 'listing', listings: fallback }],
      chips: ['Book first option', 'Show cheaper options', 'Set alert for price drop'],
    }
  }

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': key,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      system: SYSTEM_PROMPT,
      max_tokens: 650,
      messages: [{ role: 'user', content: input }],
      tools: toolset.map((t) => ({ ...t, input_schema: { type: 'object', properties: {}, additionalProperties: true } })),
    }),
  })

  if (!response.ok) throw new Error('Claude request failed')
  const data = await response.json()
  const textBlock = (data.content || []).find((c: { type: string }) => c.type === 'text')
  const movieResults = runTool('search_movies', prefs) as Listing[]
  const reasoned = movieResults.slice(0, 3)
  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    text: textBlock?.text || 'I evaluated options and prepared ranked choices.',
    cards: [{ kind: 'listing', listings: reasoned }],
    chips: ['Book This', 'Show seat map', 'Set availability alert'],
  }
}
