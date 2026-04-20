# Operator Runbook

This runbook is for the human operator during production paper mode, manual live beta, and later guarded automation stages.

## Confirm Current Mode

Check:

- `GET /api/paper/status`
- `GET /api/automation/status`
- `GET /api/execution/kill-switch`

Confirm:

- current execution mode
- whether live trading is enabled
- whether automation is enabled or paused
- current kill switch state

## Verify Health

Run:

- `GET /api/health`
- `GET /api/health/ready`
- `GET /api/health/smoke`

Look for:

- database healthy
- Redis healthy
- worker health checks passing
- no rollback recommendation

## Inspect Logs

Check CloudWatch logs for:

- `api`
- `market-stream`
- `signal-engine`
- `execution-engine`
- `notifier`

Focus on:

- repeated websocket reconnects
- Kalshi auth errors
- 429 rate-limit responses
- notification delivery failures
- reconciliation mismatches

## Confirm Kalshi Connectivity

Use smoke checks or health report to verify:

- Kalshi REST auth works
- Kalshi websocket handshake works
- exchange status reachable

Do not place orders for connectivity testing.

## Inspect Websocket Health

Review:

- market-stream health endpoint
- market-stream logs
- stale stream warnings

If reconnect loops persist, stop rollout progression.

## Inspect Signal Health

Check:

- `GET /api/signals/top`
- `GET /api/signals/overnight`

Look for:

- plausible signal volume
- explainable summaries
- no sudden unexplained alert flood

## Inspect Notification Delivery

Check:

- `GET /api/notifications/health`
- `GET /api/notifications`

Look for:

- failed deliveries
- dedupe behaving correctly
- paper/live labeling correct

## Inspect Risk Status

Check:

- `GET /api/risk`
- `GET /api/execution/kill-switch`

Look for:

- expected limits
- kill switch state
- no unexpected policy drift

## Inspect Pending Approvals

Check:

- `GET /api/approvals/pending`
- `GET /api/orders`
- `GET /api/positions`

Look for:

- orders waiting too long
- any mismatch between approval state and order state

## Trigger Or Verify Kill Switch

Use:

- `POST /api/risk/kill-switch`

Then verify:

- `GET /api/execution/kill-switch`
- `GET /api/paper/status`

Use the kill switch immediately if live behavior looks unsafe.

## Pause Automation

Use:

- `POST /api/automation/pause`
- `POST /api/automation/disable`

Then verify:

- `GET /api/automation/status`

If there is uncertainty, prefer pause first and return to manual review.

## Recover After Failure

1. move to `disabled` or `paper`
2. engage kill switch if execution safety is in doubt
3. pause automation
4. run smoke tests
5. inspect logs and affected subsystem health
6. roll back if critical health remains degraded

## Interpret Critical Alerts

Critical alerts should be treated as operator prompts, not blind execution instructions.

Read:

- market move summary
- supporting evidence
- weakening factors
- urgency tier
- suggested action

Then confirm:

- mode posture
- risk status
- whether the alert came from paper, manual live, or automation monitoring
