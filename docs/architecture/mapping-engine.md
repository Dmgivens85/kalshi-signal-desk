# Mapping Engine

The mapping engine is responsible for linking normalized external entities to Kalshi markets.

## Design Rules

- no automatic equivalence from simple keyword overlap
- every mapping carries a confidence score
- ambiguity is tracked explicitly
- mismatch reasons are preserved for future human review
- manual overrides are first-class and always win when active

## Current Strategies

- `manual_override`: explicit reviewed mapping stored in `external_market_mappings`
- `explicit_market_ref`: provider payload contains a direct market reference
- `token_similarity`: weighted token overlap and title similarity

## Stored Signals

Each mapping stores:

- `confidence_score`
- `strategy`
- `source_notes`
- `manual_override`
- `mismatch_reasons`
- `ambiguity_score`
- `feature_snapshot`

This structure is intended to support future reviewer tools and auditability.
