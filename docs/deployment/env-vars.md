# Environment Variable Strategy

Kalshi Signal Desk should treat environment variables as two groups:

- non-secret configuration values
- secret values sourced from AWS Secrets Manager or SSM Parameter Store

## Shared Mode Controls

- `EXECUTION_MODE=disabled|paper|live`
- `EXECUTION_LIVE_CONFIRMATION=true|false`
- `KALSHI_ENABLE_TRADING=true|false`

Recommended defaults:

- local: `paper`
- staging: `paper`
- production: `disabled`

Live execution should require all of the following:

- `EXECUTION_MODE=live`
- `EXECUTION_LIVE_CONFIRMATION=true`
- `KALSHI_ENABLE_TRADING=true`

## Local

Use [local.env.example](/Users/denavongivens/Downloads/Pod_Assistant/infra/env/local.env.example) for convenience values. Local may use Docker Compose managed Postgres and Redis.

## Staging

Use [staging.env.example](/Users/denavongivens/Downloads/Pod_Assistant/infra/env/staging.env.example) for non-secret coordinates.

Staging should:

- use demo Kalshi credentials
- stay in `paper` mode
- keep `KALSHI_ENABLE_TRADING=false`
- use distinct notification endpoints so staging alerts cannot be confused with production

## Production

Use [production.env.example](/Users/denavongivens/Downloads/Pod_Assistant/infra/env/production.env.example) for non-secret coordinates.

Production should start with:

- `EXECUTION_MODE=disabled`
- `EXECUTION_LIVE_CONFIRMATION=false`
- `KALSHI_ENABLE_TRADING=false`

Only after a live-readiness review should operators move toward manual-approval live mode.

## Secrets Manager / Parameter Store

Secrets that belong in AWS-managed secret stores:

- `KALSHI_API_KEY_ID`
- `KALSHI_PRIVATE_KEY_PATH` replacement strategy, or direct secret material mounted into the task securely
- `NEWS_API_KEY`
- `PUSHOVER_APP_TOKEN`
- `PUSHOVER_DEFAULT_USER_KEY`
- database credentials when not using IAM auth
- Redis auth if enabled
- `APP_JWT_SECRET`
- `SENTRY_DSN` if treated as sensitive in your environment

## Redaction Expectations

- do not log Kalshi auth headers
- do not log private key paths if they reveal secret-mount structure
- do not log full notification provider tokens
- scrub secrets from deployment job output
