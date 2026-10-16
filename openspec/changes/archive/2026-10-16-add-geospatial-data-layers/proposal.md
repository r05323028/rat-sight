# Proposal

## Why

The repository already contains the implemented Taipei administrative-boundary vertical slice from the archived `import-taipei-district-boundaries` change. This change makes that slice the explicitly verified first geospatial-data layer: it reconciles the source registry with the verified evidence, adds a non-mocked browser-to-API smoke path, and preserves the existing importer/API/MapLibre implementation rather than duplicating it.

The source is official Taipei City administrative geography, not rodent evidence. Its source version is 2022-09-15; currentness after that version remains `UNVERIFIED`.

## What Changes

- Record the verified Taipei source in the infrastructure data-source registry with an evidence link and explicit limitations.
- Add a reproducible integration smoke test that exercises the frontend against a running FastAPI endpoint and verifies the administrative layer contract without replacing the API response with a browser mock.
- Add verification and traceability for reuse of the existing importer, PostGIS persistence, versioned GeoJSON endpoint, and MapLibre administrative-reference layer.

## Scope Boundary

No new ETL framework, database, model assumption, rodent observation, infrastructure network, or biological inference is introduced. Existing implementation files remain authoritative and are reused.
