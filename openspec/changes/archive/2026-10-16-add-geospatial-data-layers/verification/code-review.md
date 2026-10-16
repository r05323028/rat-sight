# Code Review

**Decision: PASS**

Scope: actual uncommitted implementation diff for the geospatial smoke change, including `scripts/geospatial_smoke.sh`, `scripts/seed_geospatial_smoke.py`, `apps/web/playwright.config.ts`, both real-API browser specs, `infra/docker-compose.yml`, `Makefile`, source registry, and OpenSpec tasks. The planning review PASS was not treated as implementation evidence.

## Findings

### GSR-001 — HIGH / RESOLVED: smoke cleanup leaked the Next.js child process

**Resolution verified independently:** `cleanup` now recursively terminates descendants and waits for both service roots. `make geospatial-smoke` passed both real-API specs, and a post-run listener check showed no listeners on ports 3002 or 8000. The smoke can now be followed by another web e2e run without a stale Next process.

### GSR-002 — HIGH / RESOLVED: default web e2e ran external-API specs without FastAPI

**Resolution verified independently:** Both real-API specs now call `test.skip(!process.env.PLAYWRIGHT_EXTERNAL_SERVERS, ...)`. The default `corepack pnpm --filter @ratsight/web e2e` now completes **3 passed, 2 skipped** without FastAPI; the dedicated smoke command runs them with external servers enabled.

### GSR-003 — HIGH / RESOLVED: smoke seed bypassed the specified persistence/import boundary

**Resolution verified independently:** `scripts/seed_geospatial_smoke.py` now builds an EPSG:3826 GeoDataFrame, calls production `_build_batch`, `build_provenance`, and `persist_import`, and uses a SQLAlchemy transaction only for fixture cleanup/transaction ownership. The fixture remains explicitly synthetic and uses `ADMINISTRATIVE_REFERENCE`/`UNVERIFIED`.

### GSR-004 — MEDIUM / RESOLVED: unavailable dependency behavior was not explicit

**Resolution verified by source inspection:** The script now preflights Docker and emits `UNVERIFIED/NOT RUN: geospatial smoke unavailable (...)` with exit code 3 when Docker is unavailable. The documented design limitation is preserved; a no-Docker execution was not forced during this run because Docker was available.

### GSR-005 — MEDIUM / RESOLVED: fixed ports could test an unrelated/stale service

**Resolution verified by source inspection:** The script now fails closed when any fixed port is occupied and checks `kill -0` for each launched service during readiness polling. The dedicated browser response also asserts the seeded dataset's contract and identity. Fixed ports remain a deliberate local-smoke choice, but stale-service success is prevented.

## Positive observations

- The source registry entry preserves Evidence ID, official URLs, CRS, hash, license, coverage, and unresolved currentness.
- The browser specs do not intercept the administrative API; only the external basemap style is mocked. They assert data class, classification, geometry, identity, and top-level provenance.
- The compose override uses an isolated project/volume, and the script removes the stack with `down -v` plus recursive service cleanup.
- The fixture is explicitly described as synthetic and uses `ADMINISTRATIVE_REFERENCE`/`UNVERIFIED`, avoiding fabricated official geography or rodent observations.

## Verification performed

- `openspec validate add-geospatial-data-layers` — passed.
- `make geospatial-smoke` — both dedicated real-API specs passed (1 + 1); post-run checks found no listeners on ports 3002 or 8000.
- `corepack pnpm --filter @ratsight/web e2e` — **3 passed, 2 skipped**; external real-API specs are now explicitly smoke-only.
- `docker compose -f infra/docker-compose.yml config --quiet` — passed.

Original GSR-001 through GSR-005 findings were resolved before this corrective follow-up. Additional findings and post-fix review are recorded below.

## Corrective follow-up

### GSR-006 — HIGH / RESOLVED: shared Compose project let cleanup target another run

**Resolution:** Each invocation now uses a Compose project suffixed with its Bash process ID. EXIT cleanup runs `down -v` only after that invocation has begun its own `up`; Docker/port preflight exits cannot tear down a stack. Dedicated smoke passed; post-run check found no matching containers or volumes.

### GSR-007 — MEDIUM / RESOLVED: host Postgres overrides mismatched smoke API URL

**Resolution:** The smoke pins and exports `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`; it derives `DATABASE_URL` from the same variables. `env POSTGRES_DB=wrong POSTGRES_USER=wrong POSTGRES_PASSWORD=wrong POSTGRES_PORT=54320 make geospatial-smoke` passed migrations and both real-API specs.

### GSR-008 — MEDIUM / RESOLVED: smoke did not reject projected coordinates

**Resolution:** The populated browser test now asserts the first Polygon position falls within GeoJSON longitude/latitude bounds. This rejects the EPSG:3826 fixture coordinates if transformation is omitted; it is a targeted smoke assertion, not complete CRS validation for every coordinate.

### Post-fix review and verification

A three-role read-only council (correctness, infrastructure operability, requirements/test coverage) returned PASS with no concrete residual runtime defects. Review noted that fixed-port concurrency failure modes were not exhaustively exercised and the first-position assertion is narrower than full geometry validation. QA records post-fix command results; `make openspec-gate CHANGE=add-geospatial-data-layers` passed. The gate does not authenticate recorded judgments. Corrective findings GSR-006 through GSR-008 are resolved.
