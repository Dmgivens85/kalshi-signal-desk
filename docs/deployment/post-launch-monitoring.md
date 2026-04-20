# Post-Launch Monitoring

Use this checklist for the first day and first week after each rollout stage change.

## First Day

- service uptime stable
- ECS tasks stable after rollout
- websocket stability acceptable
- signal volume plausible
- overnight alert count low and understandable
- notifier failure count acceptable
- Kalshi rate-limit pressure low
- approval queue behaving normally
- reconciliation integrity intact
- no paper/live boundary issue reported

## First Week

- review false positives and weak alerts
- review confidence versus outcome
- review notification volume and dedupe effectiveness
- review manual approval throughput
- review paper PnL or live tiny-size outcomes, depending on stage
- review mobile/PWA operator issues on iPhone
- review automation status daily if any automation is enabled

## Metrics To Watch

- API readiness failures
- worker stale health states
- websocket reconnect count
- Kalshi 401/403 count
- Kalshi 429 count
- notification delivery failure count
- notification dedupe suppressions
- approval backlog size
- reconciliation mismatch count
- automation anomaly count

## Alerting Expectations

- critical opportunity and critical risk warning alerts should stay rare
- digest pathways should absorb lower-priority items
- if overnight alerts rise unexpectedly, stop rollout progression and investigate

## Automation Monitoring

If automation is enabled for any strategy:

- monitor during the first automation windows in real time
- keep size limits minimal
- require anomaly auto-disable to remain active
- revert to manual review immediately if behavior is surprising
