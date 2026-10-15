# Code Review

**Decision: PASS**

Scope: actual uncommitted implementation diff for `import-taipei-district-boundaries`, including API schemas/routes/application/persistence/importer/migration, web dashboard/MapLibre/API client/tests, and documentation. The planning review PASS was not treated as implementation evidence.

## Context proof

- **Purpose:** import one archive-verified Taipei administrative boundary layer, preserve `ADMINISTRATIVE_REFERENCE` separately from epistemic classification, expose honest GeoJSON, and render it without treating it as rodent or simulated data.
- **Invariants:** source CRS EPSG:3826 and consumer CRS EPSG:4326 are explicit; geometry and provenance fail closed; imports are archive-only and transactional/idempotent; empty is distinct from storage failure; simulation remains independent; no fabricated observations.
- **Boundaries:** importer/application/database own persistence and validation; FastAPI owns versioned response/error contracts; web owns MapLibre lifecycle and accessible states; no live download or generic ingestion.
- **Confidence:** purpose/invariants 90/100; backend implementation 85/100; frontend implementation 80/100. PostGIS integration was unavailable, so DB execution/migration constraints were inspected but not exercised.

## Findings

### CR-001 — HIGH — RESOLVED: endpoint dataset/version identity and grouping

**Resolution verified independently:** `services/api/src/ratsight_api/application/administrative_districts.py:191-220` now resolves an explicit dataset ID from settings, selects the maximum resource version within that dataset, filters both dataset and version, and `_assemble_response` rejects mixed dataset/version/archive/provenance groups. The added always-run application tests cover cross-dataset, mixed-version, mixed-hash, and mixed-provenance rows. Backend targeted tests passed (40 passed, 1 skipped).

### CR-002 — HIGH — RESOLVED: persisted geometry validation

**Resolution verified independently:** `_parse_geometry` now validates Polygon/MultiPolygon nesting, finite numeric positions, ring length/closure, Shapely validity, and the EPSG:4326 target envelope before constructing the response. Added application tests cover malformed structures, NaN/Infinity, invalid polygons, malformed multipolygons, and out-of-envelope geometry; route tests exercise the real application path. Backend targeted tests passed (40 passed, 1 skipped). PostGIS integration remains unavailable, so database constraint execution was not exercised.

### CR-003 — HIGH — RESOLVED: keyboard-accessible district selection

**Resolution verified independently:** `apps/web/src/components/dashboard.tsx:215-236` now renders an actual keyboard-focusable button for every returned district with `aria-pressed` selection state. The selected ID is passed into `MapView`; `apps/web/src/components/map-view.tsx:180-194` synchronizes a highlight layer for list or map-click selection. Vitest and Playwright coverage exercise keyboard focus/Enter, selection state, and map highlight filter behavior.

### CR-004 — MEDIUM — RESOLVED: source inspection omits the canonical source URL/license

**File:** `apps/web/src/components/dashboard.tsx:206-246`

The selected-district panel displays district ID/name, data class, classification, dataset ID, and resource version, while the canonical provenance's source URL, license, attribution, and archive hash are never shown in the inspection UI. The requirement says click inspection exposes the district name and source, and the endpoint deliberately puts complete provenance at the top level. Dataset/version identifiers are useful references but do not expose the source URL or attribution needed for provenance-aware inspection.

**Resolution verified independently:** `apps/web/src/components/dashboard.tsx:271-302` now displays source URL, attribution, license, and currentness from the canonical top-level provenance. HTTP(S) URLs become `target="_blank"` links with `rel="noopener noreferrer"`; non-HTTP values render as text. Dashboard tests assert source link attributes and attribution/currentness.

## Verification performed

- `uv run pytest services/api/tests packages/geo/tests packages/simulation/tests` — **37 passed, 1 skipped** (PostGIS integration skipped/unavailable).
- `uv run pytest services/api/tests/test_administrative_districts_import.py services/api/tests/test_administrative_districts_api.py` — **20 passed, 1 skipped**.
- `uv run ruff check services/api/src services/api/tests/test_administrative_districts_api.py services/api/tests/test_administrative_districts_import.py` — **passed**.
- `uv run basedpyright services/api/src/ratsight_api` — **0 errors, 0 warnings, 0 notes**.
- `corepack pnpm --dir apps/web test -- --run` — **12 passed**.
- `corepack pnpm --dir apps/web lint` — **passed**.
- `corepack pnpm --dir apps/web build` — **passed**.

CR-001 through CR-004 are resolved. Frontend verification passed: 13 Vitest tests, lint, and production build. Backend verification for CR-001/CR-002 passed separately (40 targeted tests, 1 skipped; PostGIS unavailable). No implementation files were edited during this re-review. `verification/gate.json` was not created; the orchestrator must record the PASS decision and finding states in the gate before acceptance.
