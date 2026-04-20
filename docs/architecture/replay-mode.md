# Replay Mode

Replay mode reuses stored Kalshi market history to evaluate how the signal engine and paper execution logic would have behaved over a historical window.

## Purpose

Replay mode is intended for:

- backtest-style validation
- overnight alert-quality review
- automation dry-run evaluation
- signal confidence calibration
- execution-assumption tuning

## Flow

1. A simulation run is created with a time window and optional ticker filter.
2. Historical market snapshots are loaded from the database.
3. Related signals in the requested window are associated with the run.
4. Replay metrics are stored on the simulation run so operators can inspect what the system would have done.

## Current Scope

The current replay implementation is intentionally pragmatic:

- it uses stored market snapshots as the historical event source
- it links matching signals for traceability
- it stores aggregate counts and summary metadata on the simulation run

This creates a durable foundation for richer event-by-event replays later, including orderbook-driven fill simulation and deeper outcome analysis.

## Future Extensions

Replay mode is designed to grow into:

- event-stream playback for ticker and orderbook deltas
- strategy-level benchmark comparisons
- per-run PnL curves
- alert quality scoring across time windows
- automated regression checks before live policy changes
