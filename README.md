# Ticketly - Agentic Ticket Booking

Production-style ticket booking platform inspired by BookMyShow/District, with a conversational booking assistant, dynamic pricing simulation, smart search, and recommendations.

## Architecture
- **Frontend**: React + Vite (UX-first layout, assistant sidebar)
- **Backend**: FastAPI + SQLModel + JWT auth
- **AI/Agentic**: Python agent orchestration with tool calls (search, recs, seats, pricing) and optional LLM integration
- **Data**: Seeded dummy movies, theatres, and showtimes

## Features
- Smart search across movies and theatres
- Personalized recommendations
- Automated seat selection
- Dynamic pricing simulation
- Conversational booking assistant
- Admin ops summary + content generation endpoint
- OAuth (Google) + OTP auth stubs

## Local Dev
### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open: `http://localhost:5173`

## Docker Compose
```bash
docker compose up --build
```

Frontend: `http://localhost:3000`
Backend: `http://localhost:8000`

## Notes
- OTP uses an in-memory store and returns `otp_debug` for demo use. Replace with Twilio or equivalent for production.
- Google OAuth requires setting `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in `backend/.env`.
- LLM integration is optional. Set `OPENAI_API_KEY` in `backend/.env`.
