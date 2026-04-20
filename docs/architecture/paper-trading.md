# Paper Trading

Paper trading gives Kalshi Signal Desk a production-like validation path without sending live orders to Kalshi.

## Design Goals

- consume real Kalshi market data
- use the real signal engine
- use the real notifier and approval flow
- simulate execution locally
- track paper positions and portfolio behavior over time
- keep the execution path as close to live as practical

## Core Flow

1. Kalshi market data is ingested through the market-stream service.
2. The signal engine produces the same alert and trade-assist outputs used in live mode.
3. The execution layer builds the same preview and approval objects used for live orders.
4. When the active mode is `paper`, submission is routed to the paper execution service instead of the live Kalshi order client.
5. Simulated orders create local paper orders, fills, positions, and portfolio snapshots.

## Simulation Rules

Paper execution supports configurable fill assumptions:

- fill strategy mode
- slippage basis points
- partial-fill ratio
- expiration behavior

The current implementation uses live market snapshots as the execution reference and applies configurable price and fill assumptions when generating simulated fills.

## Persisted Records

Paper-mode persistence includes:

- `paper_orders`
- `paper_fills`
- `paper_positions`
- `paper_portfolio_snapshots`
- `simulation_runs`

This keeps simulated activity traceable without mixing it into live order history.

## Analytics

Paper trading stores enough structure to support:

- open and closed paper positions
- realized PnL
- unrealized PnL scaffolding
- exposure by market and category
- average confidence versus outcome studies
- signal-to-order-to-outcome traceability

## Operational Value

Paper mode is meant to validate overnight behavior, approval policy tuning, automation guardrails, and notification quality before any explicit live enablement.
