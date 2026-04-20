# ECS Fargate Deployment

Kalshi Signal Desk targets Amazon ECS on AWS Fargate for staging and production.

## Service Topology

- `web`: public service behind an Application Load Balancer
- `api`: public or internal ALB-backed service depending on routing preference
- `market-stream`: internal worker service
- `external-enrichment`: internal worker service
- `signal-engine`: internal worker service
- `execution-engine`: internal worker service
- `notifier`: internal worker service
- `scheduler`: internal worker service
- `migrate`: one-off task run during deployment

## Exposure Model

Public:

- web
- api

Private:

- workers
- RDS Postgres
- ElastiCache Redis
- Secrets Manager / Parameter Store access paths

## ECS Recommendations

- use `awsvpc` networking for every task
- assign security groups at the task level
- send container logs to CloudWatch using the `awslogs` driver
- use task roles for application permissions and execution roles for image pull, logs, and secrets retrieval
- keep workers internal and avoid public IP assignment where possible

## Deployment Strategy

Staging:

- rolling deployments with ECS deployment circuit breaker
- `minimumHealthyPercent` high enough to keep at least one healthy task in place
- smoke test before operator sign-off

Production:

- start with rolling deployments plus circuit breaker
- adopt CodeDeploy blue/green only after the service graph and smoke checks are stable
- promote a previously validated image digest from staging instead of rebuilding new artifacts during production rollout

## Resource Placeholders

Reasonable starting points from `infra/ecs/service-catalog.yaml`:

- web: `512 CPU / 1024 MB`
- api: `512 CPU / 1024 MB`
- heavy workers: `512 CPU / 1024 MB`
- lighter workers: `256 CPU / 512 MB`

These should be tuned after CloudWatch metrics are available.

## Networking Assumptions

- ALB in public subnets
- ECS tasks in private subnets
- NAT or VPC endpoints for outbound access to ECR, CloudWatch, Secrets Manager, SSM, and third-party APIs
- RDS and Redis only in private subnets

## Secrets

- non-secret coordinates may live in task environment variables
- secrets should come from Secrets Manager or Parameter Store
- Kalshi private keys must never be baked into images or checked-in env files
