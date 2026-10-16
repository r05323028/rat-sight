# Design

## Existing implementation reuse

The archived `import-taipei-district-boundaries` implementation at `openspec/changes/archive/2026-10-16-import-taipei-district-boundaries` (implemented at repository revision `af975c4`) already provides the importer, additive PostGIS migration, application service, FastAPI endpoint, and MapLibre administrative-reference layer. Reused surfaces are `services/api/src/ratsight_api/importers/administrative_districts.py`, `services/api/alembic/versions/0002_administrative_districts.py`, `services/api/src/ratsight_api/api/routes/administrative_districts.py`, `services/api/src/ratsight_api/api/schemas.py`, `apps/web/src/lib/api.ts`, `apps/web/src/components/dashboard.tsx`, and `apps/web/src/components/map-view.tsx`. This change does not redesign those boundaries.

## Source and provenance

The source is the Taipei City Civil Affairs Bureau district-boundary archive documented by evidence ID `EVID-TPE-DISTRICT-BOUNDARIES-2026-10-15`. The source archive is SHP in EPSG:3826, transformed to EPSG:4326 for GeoJSON. The archive hash and license are retained by the existing importer and provenance schema. Resource currentness after 2022-09-15 remains `UNVERIFIED`.

## Integration verification

The browser smoke test uses an isolated disposable PostGIS database/container, applies Alembic migrations through `0002`, constructs one clearly marked deterministic EPSG:3826 test fixture through the production batch validation, provenance, and `persist_import` functions, starts FastAPI on `127.0.0.1:8000` and Next.js on the Playwright port with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000`, waits for both HTTP readiness endpoints, and tears down process descendants, the container, and the temporary volume in a trap. It MUST NOT intercept `/api/v1/administrative-districts` (or any application API route) with a browser route mock. The test asserts HTTP `data_state=available`, `ADMINISTRATIVE_REFERENCE`, `UNVERIFIED`, EPSG:4326 geometry, district identity, top-level provenance, and visible provenance in the dashboard; it also runs an empty-store case with no fabricated geometry. If Docker/PostGIS is unavailable, the command exits with an explicit `UNVERIFIED/NOT RUN` result rather than passing. Existing hermetic UI tests remain useful for error and empty states.

## Classification boundary

Administrative polygons are geographic context with `data_class=ADMINISTRATIVE_REFERENCE`. Their epistemic `classification=UNVERIFIED` reflects unresolved currentness and is not a claim about rodent observations. Synthetic simulation remains `SIMULATED` and independent.
