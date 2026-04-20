# Execution Engine

The execution engine is the guarded trading-control layer for Kalshi Signal Desk. It converts signals into previewable candidate orders, runs deterministic risk checks, requires explicit human approval, and only then allows server-side submission to Kalshi.

## Responsibilities

- build candidate trades from signals or direct operator input
- create deterministic previews before any submission
- persist approval state transitions
- submit orders server-side only
- reconcile later order and fill updates
- maintain auditable records for every step

## Core Modules

- `risk/engine.py`: deterministic validation and exposure checks
- `previews/service.py`: candidate construction and preview summaries
- `approvals/state_machine.py`: valid order state transitions
- `orders/service.py`: preview persistence, approval, rejection, submission, and reconciliation hooks
- `reconciliation/service.py`: fill and position updates
- `audit/service.py`: execution audit access

## State Model

- `proposed`
- `blocked`
- `pending_approval`
- `approved`
- `rejected`
- `submitted`
- `partially_filled`
- `filled`
- `canceled`
- `expired`

## Server-Side Boundary

The browser never authenticates directly to Kalshi. All Kalshi order interactions are routed through the API using the shared authenticated client and server-side credentials only.

## Data Model

- `orders`: proposed and submitted orders
- `approval_requests`: human review decisions
- `positions`: current and historical exposure
- `fills`: execution fragments linked back to orders and positions
- `risk_events`: rule failures and warnings
- `execution_audit_logs`: durable lifecycle log
