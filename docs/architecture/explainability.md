# Explainability

Every Phase 4 signal carries an explainability payload.

## Included Fields

- summary string
- top supporting factors
- top weakening factors
- source count
- confidence score
- urgency tier
- suggested action
- suggested size bucket
- evidence references

## Purpose

The UI and notifier layers should be able to show why a signal exists without re-running the scoring logic. This also makes later review, tuning, and backtesting easier because the numeric features and the human-readable explanation are persisted together.

## Current Sources

- Kalshi feature pipeline
- external enrichment feature snapshots
- policy classification results
- evidence references from mapping and catalyst inputs
