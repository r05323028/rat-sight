# Proposal

## Why

RatSight currently has no verified administrative reference geometry. Importing the official Taipei district boundary resource will provide a transparent geographic context for the dashboard without introducing rodent observations, infrastructure claims, or model assumptions.

The selected import candidate is documented in `docs/evidence/taipei-district-boundaries-2026-10-15.md` (Evidence ID `EVID-TPE-DISTRICT-BOUNDARIES-2026-10-15`). Its resource version is dated 2022-09-15; legal currency after that version remains UNVERIFIED and is retained as a user-visible limitation. The feature uses `data_class=ADMINISTRATIVE_REFERENCE` and `classification=UNVERIFIED` for that currentness limitation; it never uses biological `OBSERVED` or `SIMULATED` status.

## What Changes

- Add a minimal, deterministic importer for the documented SHP import candidate, with reproducible source verification, fail-closed CRS and geometry validation, provenance capture, and idempotent upsert behavior.
- Add additive PostGIS storage for district identifiers, names, polygon/multipolygon geometry, and source metadata.
- Expose imported districts as an EPSG:4326 GeoJSON FeatureCollection with an honest empty response when no import exists.
- Add a MapLibre administrative-boundary layer with visibility, loading/empty/error states, and district name/source inspection.
- Keep administrative reference geometry distinct from OBSERVED, INFERRED, SIMULATED, and UNVERIFIED rodent or infrastructure data.

## Capabilities

### New Capabilities

- `administrative-boundaries`: Import, persist, expose, and visualize official Taipei administrative district boundaries with provenance.

### Modified Capabilities

- None.

## Impact

Affected surfaces include an additive Alembic migration and API persistence/application layers, a documented import command and deterministic fixtures, the FastAPI contract, the web API client/dashboard/map view, and OpenSpec verification artifacts. No simulation algorithm, biological parameter, observation dataset, generic ingestion framework, or scheduled synchronization is added.
