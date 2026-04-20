# Anomaly Shutdown

Selective automation must be able to stop itself.

## Current Triggers

- repeated automation failures in a short window
- rate-limit pressure
- unusual rejection patterns
- reconciliation mismatch events
- too many automation actions in a short interval
- degraded recent service health

## Shutdown Behavior

When a strong anomaly is detected, the system:

1. records an automation failure or critical event
2. creates an active automation pause
3. emits an internal critical alert event for notifier consumption
4. falls back to manual review for later signals

## Design Intent

The objective is not to be clever about partial failure. The objective is to become conservative quickly, preserve audit context, and wait for a human operator to decide what happens next.
