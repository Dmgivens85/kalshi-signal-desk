# Overnight Alert Policy

Overnight mode is stricter than daytime mode.

## Alert Gates

An overnight alert only qualifies when all of these pass:

- `confidence_score` exceeds the overnight threshold
- liquidity/depth score clears the minimum threshold
- spread width stays below the maximum threshold
- duplicate suppression passes
- risk penalty stays below the overnight maximum
- either external confirmation exists or Kalshi-only evidence is exceptionally strong

## Classifications

- `critical_opportunity`
- `critical_risk_warning`
- `digest_only`
- `no_alert`

## Duplicate and Cooldown Behavior

- duplicate suppression uses a dedupe key and recent `alert_events`
- cooldown hooks are explicit in policy logic for future loss-based suppression
- overnight alerts default to short-lived expirations so stale opportunities age out naturally

## Why This Exists

The overnight policy is designed to wake the user rarely. The system should prefer putting marginal signals into a digest rather than escalating them into push notifications.
