# Ticketly - Autonomous AI Movie Ticket Booking Platform

Ticketly is a production-oriented AI booking assistant for high-demand movie releases such as Coolie, Leo, Salaar, and Pushpa. It monitors release openings, compares theatres, ranks seats, creates booking plans, and prepares fast checkout with seat holds and retry-aware workflows.

## What Is Implemented

- FastAPI backend with auth, movies, theatres, showtimes, recommendations, bookings, assistant workflows, admin/content APIs, and autonomous booking APIs.
- Agentic planning pipeline with intent parsing, discovery, pricing, seat selection, preference memory, workflow events, recovery, and approval plans.
- Autonomous release watch APIs for booking-open monitoring and notification creation.
- Smart seat recommendation service returning best overall, best value, and premium grouped seats.
- Provider adapter interface with demo BookMyShow-like adapter, ready for external integrations.
- Seat hold model with TTL, conflict detection, and confirmation/release workflow.
- React + TypeScript frontend redesigned as an autonomous movie booking operations cockpit.
- Go booking-engine skeleton for idempotent reservation and distributed lock semantics.
- Docker Compose with PostgreSQL, Redis, Kafka, Prometheus, and Grafana.
- Kubernetes manifests, CI workflow, HLD, LLD, API contracts, deployment guide, and dissertation notes.

## Architecture

See:

- [HLD](docs/HLD.md)
- [LLD](docs/LLD.md)
- [API Contracts](docs/API_CONTRACTS.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Dissertation Notes](docs/DISSERTATION.md)
- [Production Readiness Analysis](docs/PRODUCTION_READINESS.md)

## Production Reality

This repository is a production-grade scaffold and dissertation-ready prototype. It is designed for real public users and theatre partners, but public launch still requires live provider contracts, theatre KYC/onboarding, payment gateway hardening, webhook reconciliation, support workflows, privacy controls, and load testing under same-show contention.

The AI concierge can monitor, compare, recommend, and prepare a booking plan. It should not complete paid bookings without explicit user confirmation.

## Local Development

Backend:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Docker:

```bash
docker compose up --build
```

Frontend: `http://localhost:3000`

Backend: `http://localhost:8001`

Grafana: `http://localhost:3001`

Prometheus: `http://localhost:9090`

## Key APIs

- `POST /api/v1/assistant/message` - conversational agentic planning.
- `POST /api/v1/autonomous/seat-recommendations` - grouped smart seat ranking.
- `POST /api/v1/autonomous/release-watch` - subscribe to release openings.
- `POST /api/v1/autonomous/release-watch/run-cycle` - run demo monitor cycle.
- `GET /api/v1/autonomous/ops/dashboard` - admin operations snapshot.
- `POST /api/v1/autonomous/providers/probe` - provider adapter health/search probe.

## Research Angle

The project demonstrates autonomous workflow execution, AI-assisted theatre/seat decisioning, distributed booking coordination, retry recovery, and recommendation quality evaluation under concurrent demand.
