# Rollout Plan

Kalshi Signal Desk should move through rollout stages gradually. Do not skip directly from paper validation to broad live automation.

## Stage 1: Deployed And Smoke-Tested

Goals:

- prove deployment mechanics
- validate health endpoints, smoke checks, and rollback path

Required config:

- local or staging-safe credentials
- `EXECUTION_MODE=paper`
- `KALSHI_ENABLE_TRADING=false`

Monitoring focus:

- service health
- deploy stability
- migration health

Stop conditions:

- smoke failures
- unhealthy ECS tasks

Rollback conditions:

- critical health checks fail

## Stage 2: Staging Validated

Goals:

- validate full service graph in cloud
- confirm notifier, websocket, and paper execution behavior

Required config:

- staging environment
- demo Kalshi credentials
- paper-only

Monitoring focus:

- websocket stability
- notification delivery
- smoke-test consistency

Stop conditions:

- repeated websocket auth failures
- staging secrets or mode boundaries look unsafe

Rollback conditions:

- deployment instability or unsafe credential mix-up

## Stage 3: Production Deployed In Paper Mode

Goals:

- validate production infrastructure without live trading
- confirm operator visibility and PWA access

Required config:

- `EXECUTION_MODE=paper`
- `EXECUTION_LIVE_CONFIRMATION=false`
- `KALSHI_ENABLE_TRADING=false`

Monitoring focus:

- production health
- worker stability
- deep-link correctness

Stop conditions:

- paper/live labeling confusion
- notifier instability

Rollback conditions:

- critical production smoke failures

## Stage 4: Internal / Private Paper Validation

Goals:

- run real production flows in paper mode
- compare paper decisions against real market movement

Required config:

- production paper mode
- internal operators only

Monitoring focus:

- overnight alert quality
- signal volume
- paper fills and PnL traces

Stop conditions:

- poor alert quality
- reconciliation gaps

Rollback conditions:

- return to `disabled` if needed and fix trust issues before moving on

## Stage 5: Tiny-Size Manual Approval Live Beta

Goals:

- validate live order submission under human control
- confirm risk and approval path under real conditions

Required config:

- explicit live enablement
- manual approval only
- smallest size bucket only
- automation disabled

Monitoring focus:

- order submissions
- fills
- reconciliation
- Kalshi rate-limit pressure

Stop conditions:

- order mismatches
- elevated 429s or auth failures
- operator confusion about system posture

Rollback conditions:

- engage kill switch
- revert to `disabled` or `paper`

## Stage 6: Expanded Manual Approval Live Usage

Goals:

- widen operator coverage gradually
- keep human approval as the control point

Required config:

- explicit live enablement
- manual approval only
- conservative size limits

Monitoring focus:

- approval queue behavior
- alert-to-trade quality
- notification volume

Stop conditions:

- review backlog
- risk rule drift

Rollback conditions:

- immediate return to smaller size or paper-only if confidence drops

## Stage 7: Selective Automation Beta

Goals:

- validate one whitelisted strategy at a time
- prove anomaly shutdown behavior

Required config:

- automation enabled only for one strategy
- strongest thresholds only
- smallest automation size only

Monitoring focus:

- automation events
- anomaly triggers
- fill quality
- reconciliation integrity

Stop conditions:

- anomaly trigger
- rejection spike
- stale streams

Rollback conditions:

- pause automation immediately
- fall back to manual review

## Stage 8: Broader Guarded Automation

Goals:

- expand only after sustained evidence of safe operation

Required config:

- still default-disabled globally for new strategies
- gradual allowlist expansion

Monitoring focus:

- per-strategy performance
- risk concentration
- notification and order volume

Stop conditions:

- any safety regression

Rollback conditions:

- reduce scope back to the last known-good strategy set
