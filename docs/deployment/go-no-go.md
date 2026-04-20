# Go / No-Go Criteria

This document defines the minimum criteria required to advance Kalshi Signal Desk through rollout stages.

## Go Criteria

- all critical services healthy
- smoke tests pass
- no unsafe `live` mode configuration
- no broken approval or risk path
- no critical deployment audit issue open
- websocket stability within acceptable threshold for the rollout stage
- notifier failure rate acceptable for the rollout stage
- no unresolved reconciliation mismatch affecting trust in execution state
- paper/live separation verified

## No-Go Criteria

- any critical smoke check fails
- production is in `live` mode without explicit approval and matching env gates
- staging can reach production trading credentials
- manual approval flow is broken
- risk engine output is unavailable or inconsistent
- websocket disconnect loops persist beyond the accepted threshold
- notifier delivery failures are high enough to obscure critical alerts
- unresolved duplicate-alert storm or alert flood condition exists
- order reconciliation is missing, stale, or contradictory

## Stage-Specific Threshold Guidance

## Production Paper Mode

- no `live` execution allowed
- websocket reconnects acceptable only if streams recover quickly and remain stable
- overnight alert counts should remain low and understandable

## Manual Live Beta

- execution mode explicitly enabled and reviewed
- tiny size only
- kill switch tested before launch window
- no unresolved rate-limit pressure
- no critical order submission or reconciliation issues in the previous paper validation window

## Selective Automation

- manual live path already stable
- automation still disabled globally by default
- one strategy at a time
- stronger thresholds than manual alerts
- anomaly auto-disable path verified

## Decision Rule

If there is ambiguity, choose `no-go`, remain in `paper` or `disabled`, and resolve the issue before advancing.
