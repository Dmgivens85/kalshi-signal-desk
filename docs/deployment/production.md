# Production Deployment

Production rollout should happen only after staging has been stable in paper mode.

## Initial Production Posture

Start production in one of these states:

- `disabled` for internal validation only
- `paper` for internal validation with real production infrastructure but no live orders

Do not enable `live` during the first production infrastructure rollout.

## Recommended Sequence

1. Promote an image digest that already passed staging.
2. Run the migration task once.
3. Deploy `api`.
4. Deploy workers.
5. Deploy `web`.
6. Run post-deploy smoke tests.
7. Keep execution disabled or paper-only until operators sign off.

## Live Readiness Before Any Trading

- production observability stable
- operator runbook reviewed
- kill switch tested
- manual approval flow tested in production paper mode
- notifier deep links verified
- staging and production secrets separated
- Kalshi production credentials stored only in production secret stores

## Production Exposure

- `web` public
- `api` public or privately routed behind `web`
- workers internal only
- RDS and Redis private only

## Safer Rollout Path

1. production infrastructure with `disabled`
2. production internal validation with `paper`
3. manual-approval live beta for a small operator group
4. guarded selective automation later
