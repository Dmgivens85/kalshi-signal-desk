# Signal Engine

Phase 4 introduces the explainable signal engine for Kalshi Signal Desk.

## Purpose

- consume Kalshi-side market microstructure data
- fuse in external enrichment features and catalyst context
- score actionable decision-support signals
- classify urgency for daytime and overnight modes
- emit notifier-ready alert candidates without acting as blind execution authority

## Pipeline

1. `consumers/repository.py`
   - loads markets, snapshots, orderbook events, external mappings, and recent alerts
2. `features/kalshi.py`
   - computes momentum, move size, spread width, liquidity/depth, imbalance, volatility, time-to-resolution, and unusual activity
3. `features/fusion.py`
   - combines Kalshi features with enrichment-derived support and catalyst inputs
4. `scorers/components.py`
   - computes component scores and overall confidence
5. `policies/rules.py`
   - applies daytime/overnight alert logic, dedupe, and cooldown behavior
6. `explainability/builder.py`
   - generates structured reasons and supporting/weakening factors
7. persistence
   - stores `signals`, `signal_features`, `strategies`, and `alert_events`

## Output Shape

Each signal includes:

- `signal_id`
- `market_ticker`
- `direction`
- `confidence_score`
- `kalshi_support_score`
- `external_support_score`
- `risk_penalty_score`
- `urgency_tier`
- `suggested_action`
- `suggested_position_size_bucket`
- `reason_summary`
- `evidence_refs`
- `created_at`
- `expires_at`

## Design Intent

The engine is intentionally modular and auditable. Risk remains deterministic, and AI-oriented explanation hooks are layered on top of structured scores rather than replacing them.
