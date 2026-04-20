# Monorepo Layout

## Why This Layout

The repository is split into apps, long-running services, shared packages, infrastructure, and documentation so each concern can evolve independently without turning the platform into a single coupled backend.

## Top-Level Areas

- `apps/`
  - customer-facing and operator-facing application surfaces
- `services/`
  - continuously running background components with focused responsibilities
- `packages/`
  - reusable Python and TypeScript modules
- `infra/`
  - local containers, cloud deployment definitions, Terraform, and ECS assets
- `docs/`
  - architecture, roadmap, prompts, and operating guidance

## Intentional Separation

- `apps/api` is the long-term FastAPI home for the product-facing API shell.
- `services/*` own specialized long-running workloads.
- `packages/kalshi-client` centralizes Kalshi auth and protocol concerns.
- `packages/shared-py` and `packages/shared-ts` keep cross-service types and settings aligned.
- `packages/strategy-sdk` is where explainable strategy configuration and future plug-in style signal logic can live.
- `packages/design-system` is reserved for reusable UI tokens and components that support the premium PWA surface.
