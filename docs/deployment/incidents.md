# Incidents And Failure Modes

Use this document when Kalshi Signal Desk behaves unexpectedly during rollout or live operation.

## Websocket Disconnect Loop

Symptoms:

- repeated reconnect logs
- stale stream warnings
- falling signal freshness

Actions:

- verify market-stream health endpoint
- inspect websocket auth/connect logs
- confirm outbound networking
- pause rollout progression
- keep or move system to `paper` or `disabled` if signal trust degrades

## Kalshi Auth Failure

Symptoms:

- 401 or 403 from Kalshi
- websocket handshake failures

Actions:

- verify correct environment credentials
- verify secret rotation did not break key material
- confirm staging is not using production secrets
- do not enable live mode until resolved

## Kalshi Rate-Limit Pressure

Symptoms:

- 429 responses
- rising retries

Actions:

- reduce polling or burstiness
- inspect usage against current Kalshi API limits
- for current official guidance, Kalshi documents read/write account tiers such as Basic `20/s` read and `10/s` write, with higher tiers above that
- keep automation disabled or reduce activity if pressure rises

This is based on Kalshi’s current official rate-limit docs as of April 20, 2026.

## Notifier Outage

Symptoms:

- `/api/notifications/health` degraded
- delivery failures rise

Actions:

- inspect Pushover response codes
- verify token and user key
- fall back to dashboard monitoring if alerts are unreliable
- do not widen rollout while alerting is impaired

## Duplicate Alert Storm

Symptoms:

- repeated similar alerts
- overnight alert volume unexpectedly high

Actions:

- inspect dedupe and cooldown settings
- pause automation if enabled
- reduce operator noise before continuing rollout

## Paper / Live Mode Confusion

Symptoms:

- UI or notifications unclear about mode
- production mode not matching expectation

Actions:

- check `/api/paper/status`
- check env vars and live gates
- move to `disabled` if there is any doubt

## Order Reconciliation Mismatch

Symptoms:

- order state inconsistent with fills or positions

Actions:

- stop advancing rollout
- inspect execution audit logs
- verify Kalshi order fetch paths
- use manual review until state trust is restored

## Automation Anomaly Trigger

Symptoms:

- automation paused automatically
- anomaly events or failure counts spike

Actions:

- keep automation paused
- review events and failures
- return to manual approval flow

## DB Outage

Symptoms:

- `/api/health/ready` fails on database

Actions:

- inspect RDS health
- fail closed on rollout
- keep execution disabled until DB health is restored

## Redis Outage

Symptoms:

- readiness degraded
- dedupe or queue behavior impaired

Actions:

- inspect Redis connectivity
- treat notifications and automation conservatively until restored

## Migration Failure

Symptoms:

- migration task fails
- app starts but schema mismatches appear

Actions:

- stop deployment
- do not continue rollout
- prefer app rollback over risky schema rollback unless rehearsed

## Bad Deployment Requiring Rollback

Symptoms:

- critical smoke failures
- health endpoints degrade after rollout

Actions:

- use rollback runbook
- keep or move execution to `disabled`
- verify rollback success with smoke tests before resuming traffic

## Notification Quota Or 429 Pressure

Symptoms:

- Pushover quota near exhaustion
- API failures indicating quota or temporary service issues

Actions:

- inspect Pushover usage headers or quota endpoint
- remember current official Pushover guidance still documents a free monthly allowance of `10,000` messages per application, with usage visible through response headers and API endpoints
- keep overnight alerts selective
- verify dedupe and digest routing are working

This reflects current official Pushover docs available on April 20, 2026.
