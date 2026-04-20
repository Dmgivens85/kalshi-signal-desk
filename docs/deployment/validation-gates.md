# Validation Gates

Recommended rollout gates for Kalshi Signal Desk:

## Gate 1: Build

- images build successfully
- unit and API tests pass

## Gate 2: Staging Deploy

- ECS services become stable
- migration task completes
- smoke tests pass

If this gate fails, do not promote.

## Gate 3: Staging Review

- paper mode confirmed
- operator UI reachable
- notification and worker health reviewed

## Gate 4: Production Deploy

- promote the exact image digest validated in staging
- run migrations once
- deploy services in controlled order
- smoke tests pass

## Gate 5: Production Safety Review

- execution mode posture confirmed
- kill switch visible
- automation status reviewed
- no accidental live credentials or live mode drift

Only after this should operators consider moving beyond disabled or paper posture.
