# Kalshi Signal Desk

Kalshi Signal Desk is a production-oriented, cloud-native Kalshi market intelligence and guarded trade-assist platform.

The product philosophy is:

- monitor broadly
- enrich intelligently
- alert rarely
- explain clearly
- execute cautiously

## Proposed Structure

```text
kalshi-signal-desk/
  apps/
    api/
    web/
  services/
    market-stream/
    external-enrichment/
    signal-engine/
    execution-engine/
    notifier/
    scheduler/
  packages/
    shared-py/
    shared-ts/
    strategy-sdk/
    design-system/
    kalshi-client/
  infra/
    docker/
    compose/
    ecs/
    env/
    scripts/
    terraform/
  docs/
    architecture/
    deployment/
    roadmap/
    prompts/
```

## Current Deliverables

- Phase 2 Kalshi core integration
- Phase 3 external enrichment services
- Phase 4 signal engine and high-confidence alert scoring
- Phase 5 notifier service and Pushover delivery
- Phase 6 execution controls, risk engine, and manual approval flow
- Phase 7 selective automation with strict guardrails
- Phase 8 paper trading and replay mode
- Phase 9 staging and production deployment preparation
- Phase 10 post-deployment smoke tests and deployment validation
- Phase 11 go-live readiness, rollout checklist, and operational launch plan

## Local Development

1. Copy `.env.example` to `.env`
2. Install JavaScript dependencies with `pnpm install`
3. Start local services with `docker compose up --build`
4. Open:
   - web: `http://localhost:3000`
   - API docs: `http://localhost:8000/docs`

## Safe Mode Defaults

Keep local and staging in a non-live posture:

- `EXECUTION_MODE=paper`
- `EXECUTION_LIVE_CONFIRMATION=false`
- `KALSHI_ENABLE_TRADING=false`

Live execution should never happen accidentally. It requires all three live gates to be enabled explicitly.

## Paper Trading

Paper mode uses real market data, the real signal engine, and the real notifier pipeline while simulating orders and fills locally.

Useful routes:

- `GET /api/paper/status`
- `GET /api/paper/orders`
- `GET /api/paper/positions`
- `GET /api/paper/performance`
- `POST /api/paper/replay/start`

## Deployment Assets

- ECS/Fargate service catalog: [infra/ecs/service-catalog.yaml](/Users/denavongivens/Downloads/Pod_Assistant/infra/ecs/service-catalog.yaml)
- Task definition templates: [infra/ecs/task-definitions](/Users/denavongivens/Downloads/Pod_Assistant/infra/ecs/task-definitions)
- Environment templates: [infra/env](/Users/denavongivens/Downloads/Pod_Assistant/infra/env)
- Runtime Dockerfiles: [infra/docker](/Users/denavongivens/Downloads/Pod_Assistant/infra/docker)
- Deployment scripts: [infra/scripts](/Users/denavongivens/Downloads/Pod_Assistant/infra/scripts)

## Deployment Notes

- staging should remain `paper` mode and use demo Kalshi credentials
- production should start in `disabled` or `paper`, not `live`
- worker services should remain internal-only
- PWA installs on iPhone require Safari, HTTPS, and manual Add to Home Screen

## Key Docs

Architecture:

- [Kalshi Integration](/Users/denavongivens/Downloads/Pod_Assistant/docs/architecture/kalshi-integration.md)
- [External Enrichment](/Users/denavongivens/Downloads/Pod_Assistant/docs/architecture/external-enrichment.md)
- [Signal Engine](/Users/denavongivens/Downloads/Pod_Assistant/docs/architecture/signal-engine.md)
- [Execution Engine](/Users/denavongivens/Downloads/Pod_Assistant/docs/architecture/execution-engine.md)
- [Selective Automation](/Users/denavongivens/Downloads/Pod_Assistant/docs/architecture/selective-automation.md)
- [Paper Trading](/Users/denavongivens/Downloads/Pod_Assistant/docs/architecture/paper-trading.md)
- [Replay Mode](/Users/denavongivens/Downloads/Pod_Assistant/docs/architecture/replay-mode.md)
- [Execution Modes](/Users/denavongivens/Downloads/Pod_Assistant/docs/architecture/execution-modes.md)

Deployment:

- [Staging](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/staging.md)
- [Production](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/production.md)
- [ECS Fargate](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/ecs-fargate.md)
- [Env Vars](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/env-vars.md)
- [Runbook](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/runbook.md)
- [Rollback](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/rollback.md)
- [Smoke Tests](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/smoke-tests.md)
- [Go-Live Checklist](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/go-live-checklist.md)
- [Go / No-Go](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/go-no-go.md)
- [Rollout Plan](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/rollout-plan.md)
- [Operator Runbook](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/operator-runbook.md)
- [Incidents](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/incidents.md)
- [Post-Launch Monitoring](/Users/denavongivens/Downloads/Pod_Assistant/docs/deployment/post-launch-monitoring.md)

## Notes

- `apps/api` is the long-term backend home for the product shell.
- `services/api` contains the deeper implementation already built in this repo.
- external venues are enrichers only in v1.
- Kalshi remains the only execution venue in v1.
