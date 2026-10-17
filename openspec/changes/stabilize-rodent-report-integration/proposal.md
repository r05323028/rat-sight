# Proposal

## Why

The fixture-only rodent-report integration is implemented, but stabilization review identified a smoke harness conflict with the production immutability trigger, a classification consistency gap, an unbounded auxiliary report list, incomplete real-map interaction coverage, and misleading invalid temporal-filter feedback.

## What Changes

- Make the disposable smoke reset compatible with immutable production persistence without weakening the trigger.
- Enforce `SIMULATED` consistently in rodent-report persistence and API reads, failing explicitly on inconsistent stored data.
- Bound the auxiliary report list to 100 while preserving all MapLibre features and map selection.
- Add real-browser map-point selection and layer-disable/stale-selection assertions.
- Validate invalid temporal ranges before issuing API requests and show a clear UI message.

No external report data, new framework, generic abstraction, scientific claim, or simulation integration is introduced.
