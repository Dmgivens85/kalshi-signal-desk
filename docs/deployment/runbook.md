# Deployment Runbook

## Build

Use:

- [build-images.sh](/Users/denavongivens/Downloads/Pod_Assistant/infra/scripts/build-images.sh)
- [push-images.sh](/Users/denavongivens/Downloads/Pod_Assistant/infra/scripts/push-images.sh)

Recommended CI/CD sequence:

1. build immutable image tags from a commit SHA
2. push images to ECR
3. deploy to staging
4. run smoke tests
5. require operator approval for promotion
6. promote the same image digest to production
7. verify health and execution-mode safety

## Migrate

Run migrations as a one-off ECS task or from a controlled operator shell using:

- [run-migrations.sh](/Users/denavongivens/Downloads/Pod_Assistant/infra/scripts/run-migrations.sh)

Never rely on every service startup to race migrations in staging or production.

## Deploy

For each service update:

1. register the new task definition revision
2. deploy with [deploy-ecs.sh](/Users/denavongivens/Downloads/Pod_Assistant/infra/scripts/deploy-ecs.sh)
3. wait for ECS service stability
4. run smoke tests

## Smoke Test

Run:

- [smoke-test.sh](/Users/denavongivens/Downloads/Pod_Assistant/infra/scripts/smoke-test.sh)

Recommended checks:

- web health
- API liveness and readiness
- notifier health
- automation status
- paper status safety
- websocket-driven workers healthy
- no accidental `live` mode activation

## PWA Notes

- production and staging should both use HTTPS
- validate that the manifest loads correctly
- validate deep links from notification payloads
- on iPhone, installs happen through Safari using Share -> Add to Home Screen

## Failure Handling

If health checks fail:

1. stop promotion
2. inspect ECS service events and CloudWatch logs
3. roll back to the previous task definition
4. verify service stability
