# Staging Deployment

Staging is the first cloud deployment target and should always be safer than production.

## Staging Principles

- paper mode only
- demo Kalshi credentials only
- internal operator use only
- validate deployability, data flow, alerts, approvals, and paper execution before any production promotion

## Recommended AWS Shape

- one ECS cluster for staging
- Fargate services for web, api, and all workers
- one public ALB for web and api
- one RDS Postgres instance
- one ElastiCache Redis instance
- CloudWatch logs and alarms
- Secrets Manager / Parameter Store for credentials

## Deployment Sequence

1. Build and tag images.
2. Push images to ECR.
3. Register updated ECS task definitions.
4. Run the migration task once.
5. Deploy `api` first.
6. Deploy internal workers.
7. Deploy `web` last.
8. Run smoke tests.

## Staging Safety Gates

- `EXECUTION_MODE=paper`
- `EXECUTION_LIVE_CONFIRMATION=false`
- `KALSHI_ENABLE_TRADING=false`
- `KALSHI_ENV=demo`

## Operator Checks

- `web` and `api` ALB targets healthy
- `/api/health/ready` returns healthy
- `/api/paper/status` returns `paper`
- signal engine produces signals
- notifier labels alerts as paper when they imply execution
- no service is using production secrets
- the PWA is reachable over HTTPS and can be added to the iPhone Home Screen from Safari
