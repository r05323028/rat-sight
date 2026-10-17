# Proposal

## Why

RatSight currently has no inspectable rodent-report layer. The source investigation found no candidate with verified reuse, privacy, schema, CRS, and coverage terms. Rat Radar exposes public report metadata but its license, privacy, coordinate policy, and redistribution permissions remain unverified; Taipei 1999/open-data candidates lack a verified dataset contract.

Evidence: `docs/evidence/rodent-report-source-investigation-2026-10-17.md`.

## What Changes

- Add a minimal local-file-only importer and additive PostGIS persistence for a documented fixture-compatible rodent-report contract.
- Add bounded spatial and temporal API queries with explicit empty/error states and typed provenance.
- Add an independent dashboard layer with temporal controls, report selection, source attributes, and evidence limitations.
- Keep fixtures explicitly `SIMULATED`; do not ingest or redistribute real citizen reports.

## Scope and Integrity Boundary

Fixture records represent synthetic report-shaped data only. They are not observations, prevalence, population, movement, disease risk, or intervention evidence. Any future real source requires explicit data-owner authorization, license/reuse terms, privacy/retention review, field semantics, CRS/precision, and human acceptance before import. No report layer is connected to simulation or infrastructure topology.
