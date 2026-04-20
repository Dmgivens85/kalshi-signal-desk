# ECS Deployment Assets

This directory holds staging-first ECS/Fargate deployment scaffolding for Kalshi Signal Desk.

## Contents

- `service-catalog.yaml`: service exposure, sizing, and runtime role guidance
- `task-definitions/`: task-definition templates for web, api, and worker classes

## Service Model

- `web`: public ECS service behind an internet-facing ALB
- `api`: public ECS service behind an internet-facing or private ALB, depending on routing choice
- workers: internal-only ECS services without public ingress
- `migrate`: one-off Fargate task run before application promotion

## Deployment Recommendations

- use rolling deployments with deployment circuit breaker in staging
- keep old tasks serving until new tasks pass health checks
- use blue/green for production only after the staging path is stable and smoke-tested
- keep staging on paper mode with demo Kalshi credentials
- keep production in `disabled` or `paper` mode until live-readiness review is complete
