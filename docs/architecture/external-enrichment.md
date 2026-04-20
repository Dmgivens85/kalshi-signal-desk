# External Enrichment

Phase 3 introduces the external enrichment layer for Kalshi Signal Desk.

## Purpose

- ingest outside context from sportsbook APIs, forecast platforms, and news feeds
- normalize heterogeneous source formats into a shared schema
- map external entities to Kalshi markets without assuming equivalence from keyword overlap alone
- compute reusable enrichment features for downstream signal scoring

External providers are enrichers only. They are not execution venues.

## Core Components

- `services/external-enrichment`: worker service for ingestion, normalization, mapping, and derived feature generation
- `packages/shared-py/src/kalshi_signal_shared/enrichment.py`: shared normalized models
- `external_sources`: source registry and health
- `external_entities`: normalized external market/question/article records
- `external_observations`: append-only snapshots and article observations
- `external_market_mappings`: confidence-scored mappings plus manual overrides and ambiguity tracking

## Source Categories

- sportsbook adapters for implied probability, consensus, and divergence features
- forecast adapters for Polymarket, Metaculus, and Manifold
- news adapter for article/catalyst ingestion with AI-ready metadata fields

## Feature Outputs

The worker computes and stores mapping-level feature snapshots with:

- `external_support_score`
- `consensus_delta`
- `disagreement_score`
- `source_count`
- `recency_score`
- `catalyst_presence`

These are designed to be consumed later by the signal engine rather than acting as trade authority.
