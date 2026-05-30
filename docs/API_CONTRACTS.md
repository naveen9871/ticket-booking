# API Contracts

## Autonomous Booking

`POST /api/v1/assistant/message`

```json
{
  "message": "Book 4 tickets for Coolie tomorrow evening near Whitefield",
  "context": { "session_key": "guest-123", "city": "Bengaluru" }
}
```

`POST /api/v1/autonomous/seat-recommendations`

```json
{
  "showtime_id": 101,
  "party_size": 4,
  "session_key": "guest-123",
  "price_ceiling": 500,
  "ideal_row_ratio": 0.62
}
```

`POST /api/v1/autonomous/release-watch`

```json
{
  "movie_title": "Coolie",
  "city": "Bengaluru",
  "preferred_formats": ["IMAX", "Dolby"],
  "preferred_theatres": ["PVR Orion Mall"],
  "price_ceiling": 500,
  "party_size": 4,
  "auto_reserve": true
}
```

`POST /api/v1/autonomous/release-watch/run-cycle`

Runs the demo monitor cycle. In production this is executed by a scheduler or Kafka consumer.

`GET /api/v1/autonomous/ops/dashboard`

Returns demand, provider, queue, and SLO status for admin dashboards.

## Booking

`POST /api/v1/bookings`

```json
{
  "showtime_id": 101,
  "seats": ["F7", "F8", "F9", "F10"],
  "hold_token": "optional-hold-token",
  "session_key": "guest-123"
}
```

## Provider Probe

`POST /api/v1/autonomous/providers/probe`

```json
{
  "provider_code": "BMS_DEMO",
  "payload": {
    "movie": "Coolie",
    "city": "Bengaluru"
  }
}
```

