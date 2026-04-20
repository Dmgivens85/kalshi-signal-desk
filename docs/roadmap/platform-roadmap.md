# Platform Roadmap

## Phase 0

- normalize repository layout
- establish Docker and local Compose workflow
- publish architecture and roadmap docs
- preserve useful implementation work already in progress

## Phase 1

- complete `apps/api` migration path from legacy service code
- stand up Postgres-backed models and migrations under the long-term app location
- harden Kalshi client packaging and stream lifecycle
- wire notifier and execution service boundaries cleanly through queues or APIs

## Phase 2

- real Kalshi market list and websocket ingestion
- external enrichers for sportsbook, Polymarket, Metaculus, Manifold, and news
- confidence-based mapping with manual overrides
- explainable signal engine with evidence references

## Phase 3

- high-confidence overnight mode
- iPhone push routing through Pushover
- morning digest workflow
- operator controls for watchlists, strategies, and notification preferences

## Phase 4

- ECS Fargate deployment assets
- observability and incident tooling
- selective automation architecture with explicit opt-in and guardrails
