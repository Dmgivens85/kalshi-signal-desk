# Rollback

Rollback should be simple, explicit, and tested in staging.

## Preferred Rollback Strategy

- keep the last known-good task definition ARN for every service
- roll back one service at a time
- verify health after each rollback

Use:

- [rollback-ecs.sh](/Users/denavongivens/Downloads/Pod_Assistant/infra/scripts/rollback-ecs.sh)

## When To Roll Back

- ALB health checks fail
- `/api/health/ready` fails
- worker health endpoints become stale
- migration caused an unexpected incompatibility
- notifier or execution mode safety checks behave incorrectly

## Database Rollback Notes

Schema rollback is often riskier than application rollback. Prefer:

- backward-compatible migrations
- application rollback first
- schema rollback only when explicitly rehearsed and necessary

## Mode Safety During Rollback

If anything is ambiguous:

- set `EXECUTION_MODE=disabled`
- keep `EXECUTION_LIVE_CONFIRMATION=false`
- keep `KALSHI_ENABLE_TRADING=false`

This ensures rollback work cannot accidentally trigger live trading behavior.
