# Architecture Overview

## Goals

- Separate user experience, API orchestration, and asynchronous processing into independently deployable units.
- Share schemas and clients across services to keep product, research, and execution workflows aligned.
- Support local-first development with Docker while staying ready for cloud deployment on Kubernetes, ECS, or Nomad.

## Proposed Layout

- `apps/web`: Next.js frontend for dashboards, analyst tooling, and signal review.
- `services/api`: FastAPI control plane for market metadata, auth, orchestration, and downstream integrations.
- `services/worker`: Python worker service for ingestion, enrichment, scoring, and scheduled jobs.
- `packages/ui`: Shared React UI primitives for consistent platform experiences.
- `packages/typescript-sdk`: Shared frontend SDK and typed service contracts.
- `packages/python-common`: Shared Pydantic models, settings, and Python utilities.
- `infra/terraform`: Cloud infrastructure modules and environment definitions.
- `docs/runbooks`: Operating guides for incidents, deployments, and data backfills.

## Local Runtime

- `web` runs on port `3000`
- `api` runs on port `8000`
- `postgres` runs on port `5432`
- `redis` runs on port `6379`
