# Go-Live Checklist

Use this checklist before any change in production posture, especially before moving from `disabled` or `paper` toward manual live approval.

## Environment And Secrets

- production environment variables reviewed and match the intended stage
- `EXECUTION_MODE` verified
- `EXECUTION_LIVE_CONFIRMATION` verified
- `KALSHI_ENABLE_TRADING` verified
- production secrets loaded from Secrets Manager or Parameter Store
- staging and production Kalshi credentials confirmed separate
- staging does not have production trading credentials
- Pushover tokens and recipients verified for the intended environment

## Safety Controls

- global kill switch path verified
- kill switch currently in the intended state
- automation globally disabled unless the rollout stage explicitly allows it
- automation per-strategy policies remain disabled by default
- paper/live UI labeling verified on web and notification surfaces
- manual approval path verified in the current environment

## Platform Health

- DB migrations applied successfully
- `/api/health` green
- `/api/health/ready` green
- `/api/health/smoke` passes
- worker health endpoints green
- websocket connectivity stable
- notifier health green
- Redis connectivity healthy
- database connectivity healthy

## Trading And Risk Readiness

- Kalshi connectivity verified without placing orders
- Kalshi REST auth check passes
- Kalshi websocket auth/connect check passes
- rate-limiting and throttling settings reviewed
- audit logging enabled
- risk engine status reviewed
- pending approval queue visible and functioning
- reconciliation status has no unresolved critical issues

## Deployment Safety

- rollback task definition or prior service revision recorded
- rollback operator identified
- operator contacts documented
- runbook location shared with launch participants
- smoke tests completed after the current deployment revision

## Go-Live Decision

Go live only if:

- all critical health checks pass
- no paper/live boundary issues are open
- no websocket instability is above the accepted threshold
- no unresolved order or reconciliation issue is open
- no critical notification delivery problem is open
