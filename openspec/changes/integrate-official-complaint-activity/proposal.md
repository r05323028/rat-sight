# Proposal

## Why

RatSight currently has no verified municipal complaint-activity layer. Taipei City Government dataset `cb423c17-88eb-4231-a725-f1b93247d1bf` may provide historical complaint activity, but implementation is conditional on proving source terms, schema, record grain, and an exact official rodent-category mapping.

## What Changes

- Phase A: verify official metadata, resources, license, CSV schema/encoding, category values, record grain, dates, duplicates, coverage, and rodent-specific classification.
- Phase B-D only if the feasibility gate is GO: define a minimal monthly aggregate contract, local fail-closed importer, versioned aggregate API, and compact dashboard trend view.
- If the gate is NO-GO, record evidence and stop without migrations, API, UI, or fabricated statistics.

## Integrity Boundary

Complaint activity is an official administrative record, not an `OBSERVED` rodent sighting, prevalence estimate, population estimate, intervention effect, or movement input. No fuzzy text classification, geographic inference, simulation integration, or individual complaint exposure is permitted.
