# Notification Policy

The notification policy is designed to support the product rule: alert rarely and explain clearly.

## Delivery Classes

- `critical_opportunity`: wake-capable overnight opportunity with strong support
- `critical_risk_warning`: wake-capable overnight risk or adverse move
- `daytime_alert`: send during daytime if preferences allow it
- `digest_only`: persist for later review but do not send immediately

## Quiet Hours

- quiet hours suppress ordinary alerts
- overnight critical alerts may bypass quiet hours
- quiet hours remain user-configurable through `quiet_hour_policies`

## Dedupe

- delivery uses `dedupe_key` plus TTL-based suppression
- Redis is the fast path
- the database is the fallback path when Redis is unavailable
- repeated alerts for the same signal window are suppressed unless the key changes

## Overnight Standards

Only `critical_opportunity` and `critical_risk_warning` are eligible to wake the user overnight. Lower-priority items remain available for the morning digest.

## Deep Links

Notifications are expected to route back into the PWA with paths such as:

- `/signals/{id}`
- `/markets/{ticker}`
- `/risk`
- `/orders/{id}`
