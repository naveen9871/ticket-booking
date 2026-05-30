# Dissertation Notes

## Research Theme

Autonomous AI-assisted booking during high-contention ticket releases.

## Research Questions

1. How much can agentic planning reduce user interactions during a high-demand booking flow?
2. Can hybrid ranking improve perceived seat quality compared with price-only or center-only ranking?
3. How does queue-based booking coordination affect success rate under concurrent contention?
4. How well do retry workflows recover from provider failures and seat races?

## Evaluation Metrics

| Metric | Definition |
| --- | --- |
| Booking success rate | Confirmed bookings divided by attempted bookings |
| Interaction reduction | Manual clicks/searches avoided by the assistant |
| Recommendation quality | User acceptance rate of top-ranked seat/theatre suggestions |
| Booking latency | Time from confirmation click to hold/payment result |
| Retry success rate | Failed reservation attempts later recovered |
| Concurrency safety | Duplicate booking incidents per million attempts |
| AI accuracy | Intent parse correctness and plan acceptance |

## Experiment Design

Run load tests with 100, 1,000, and 10,000 simulated users targeting the same show. Compare:

- manual search baseline,
- deterministic filters,
- AI-ranked theatre and seat plans,
- AI-ranked plans plus queue-based reservation.

Expected result: queueing and idempotent locking reduce duplicate booking failures, while agentic ranking reduces average interaction count and improves top-option acceptance.

