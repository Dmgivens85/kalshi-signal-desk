# Provider Adapters

Provider-specific logic is isolated behind adapter classes in `services/external-enrichment/src/external_enrichment/providers`.

## Adapter Contract

Each provider implements:

- `fetch_entities(...)`
- `fetch_markets_or_questions(...)`
- `fetch_observations(...)`
- `normalize(...)`
- `healthcheck(...)`

## Current Adapters

- `SportsbookPrimaryAdapter`
- `SportsbookSecondaryAdapter`
- `PolymarketAdapter`
- `MetaculusAdapter`
- `ManifoldAdapter`
- `NewsProviderAdapter`

## Extension Pattern

To add a provider later:

1. create a new adapter class under `providers/`
2. use a `normalizers/` helper when the raw payload format deserves its own translation logic
3. emit `ExternalEntityModel` and `ExternalObservationModel`
4. register the adapter in the worker service
5. add any provider-specific health or auth env vars

This keeps provider code isolated and prevents source-specific assumptions from leaking into the rest of the system.
