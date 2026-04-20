# System Overview

## Product Intent

Kalshi Signal Desk is an always-on Kalshi market intelligence and trade-assist platform built to:

- run continuously in the cloud
- monitor Kalshi in real time
- enrich Kalshi signals with external context
- alert only when confidence is high
- keep execution deterministic, explainable, and approval-gated

## Core Product Rules

- Kalshi is the only execution venue in v1.
- External venues are enrichers only.
- AI improves summarization, ranking, relevance, and explanation, but does not override deterministic risk rules.
- Overnight push notifications are reserved for high-confidence critical opportunity and critical risk alerts.
- Autonomous trading is not enabled by default.

## Service Topology

- `apps/web`: mobile-first installable PWA
- `apps/api`: primary FastAPI application shell
- `services/market-stream`: authenticated Kalshi websocket ingestion
- `services/external-enrichment`: sportsbook, forecast, and news enrichment collectors
- `services/signal-engine`: feature fusion, scoring, ranking, and explanation
- `services/execution-engine`: order preview, approval workflow, deterministic risk checks, cautious submission
- `services/notifier`: Pushover-first delivery and future web-push abstraction
- `services/scheduler`: periodic jobs, stale-stream detection, health checks, digest generation

## Reliability Principles

- reconnect with exponential backoff
- idempotent order submission
- duplicate suppression on alerts and notifications
- service health endpoints for every component
- structured logs for all critical workflows
- dead-letter handling for failed notifications
- replay-friendly event storage where practical
- kill switch and audit logging for all execution-sensitive paths

## Deployment Direction

The long-term deployment target is AWS ECS Fargate with:

- separate service definitions per long-running component
- Postgres for relational state
- Redis for queue/cache/coordination
- centralized log shipping
- metrics and tracing hooks
- Sentry-style error capture
