# Manual Approval Flow

Manual approval is required in v1. The platform can rank and explain opportunities, but a human must still decide whether a proposed order is allowed to proceed.

## Flow

1. A signal or operator request creates an order preview.
2. The risk engine evaluates the proposed trade deterministically.
3. If blocked, the order is stored with clear reasons.
4. If allowed, the order enters `pending_approval`.
5. A human approves or rejects it through the API or mobile web UI.
6. Only approved orders may be submitted server-side to Kalshi.
7. Reconciliation later updates the order, fills, and positions.

## Mobile UX

The Phase 6 PWA includes:

- an approvals queue
- an order preview detail sheet
- a position overview
- a risk dashboard with kill-switch visibility

These pages are designed for quick review from an iPhone rather than dense desktop-only workflows.

## Future Path

Selective automation can be added later by changing policy around which approved strategies may auto-submit. The current architecture supports that path without enabling unrestricted autonomy today.
