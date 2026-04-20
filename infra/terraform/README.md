# Terraform Scaffolding

Terraform remains intentionally lightweight, but it now reflects separate staging and production environment entry points.

## Environments

- `environments/dev/`: local or sandbox cloud experiments
- `environments/staging/`: staging ECS/Fargate environment, paper mode only
- `environments/production/`: production ECS/Fargate environment, live disabled by default

## Expected Module Split

- `network`
- `ecs-cluster`
- `ecs-service`
- `rds-postgres`
- `elasticache-redis`
- `secrets`
- `observability`

## Guardrails

- use distinct AWS accounts or at minimum distinct VPCs and secrets for staging vs production
- never share Kalshi production credentials with staging
- default production execution mode to `disabled`
- run migrations as a one-off task, not as part of every service startup
