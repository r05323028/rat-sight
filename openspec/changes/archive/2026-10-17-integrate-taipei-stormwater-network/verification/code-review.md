# Independent implementation code review

**Reviewer:** verification-reviewer  
**Scope:** actual stormwater implementation diff, backend importer/API/persistence/tests, frontend API/dashboard/MapView/tests/E2E, smoke/official verification artifacts, simulation positive-visit filtering, and OpenSpec contract alignment.  
**Decision:** PASS.

## Context proof

- **Subsystem purpose:** provide a provenance-preserving Taipei stormwater infrastructure reference layer through a local archive-only importer, additive PostGIS persistence, bounded EPSG:4326 GeoJSON, and an independent dashboard layer.
- **Key invariants:** infrastructure is `INFRASTRUCTURE_REFERENCE` and `UNVERIFIED`; it is not rodent evidence, inferred connectivity, traversability, risk, or simulation input. Candidate B identity/hash and CRS must be verified. Source `識別碼` is persistence identity; public API identity is opaque `segment_id`. Z is dropped because its vertical datum is undocumented. Bbox queries are finite and capped. Synthetic map edges with zero visits are not rendered.
- **Architecture boundaries:** FastAPI owns contracts/persistence integration; frontend consumes JSON only; geometry conversion remains in importer; simulation remains independent. Official verification is isolated and not a regular test.
- **Expected behavior:** archive-only import, transactional/idempotent persistence, typed provenance, bounded API, lifecycle-safe MapLibre layer, honest empty/error/partial states.
- **Unknowns:** official source bytes were not available in the repository; PostGIS-backed persistence and the isolated official script were not run in this review environment.
- **Confidence:** contract/spec 92/100; backend code 88/100; frontend code 88/100; verification evidence 75/100 because live PostGIS/browser official checks were not run.

## Findings

### CR-001 — HIGH / RESOLVED: CRS validation accepted non-EPSG:3826 identifiers

**Resolution verified:** `importer.py` now normalizes `srsName` and requires exact `EPSG:3826`; `test_near_match_srs_name_is_rejected` verifies that `EPSG:13826` fails. The required exact 3D dimension check remains present.

### CR-002 — MEDIUM / RESOLVED: selected pipeline remained inspectable after an in-view miss

**Resolution verified:** `dashboard.tsx` now derives `selectedVisibleSegment` from the current response and returns `null` for error, empty, or absent selected IDs. Details and selection highlighting therefore disappear without state-setting effects.

### CR-003 — HIGH / RESOLVED for the documented command: importer identity was overrideable

**Resolution verified:** `main()` now pins Candidate B dataset/resource/version/archive hash unless the explicit `--allow-nonofficial-source` test-fixture flag is supplied. The documented production command therefore cannot silently relabel the Candidate B archive with another source identity. The lower-level test helper remains parameterized for deterministic fixtures, as intended.

### CR-004 — LOW / RESOLVED: targeted backend lint failed on the changed importer

**Resolution verified:** the long `srsDimension` error string is now wrapped; targeted Ruff checks pass.

## Verification run

- `uv run --package ratsight-api pytest services/api/tests/test_stormwater_pipelines_import.py services/api/tests/test_stormwater_pipelines_api.py` — **35 passed**.
- `corepack pnpm --filter @ratsight/web test -- --run apps/web/src/components/dashboard.test.tsx apps/web/src/components/map-view.test.tsx apps/web/src/lib/api.test.ts` — **28 passed**.
- `corepack pnpm --filter @ratsight/web build` — **passed**.
- Targeted `uv run --package ratsight-api ruff check ...` — **passed**.
- `openspec validate integrate-taipei-stormwater-network` — **valid**, with three long-requirement warnings.
- `scripts/verify_official_districts.sh` — **not run**; this review did not claim official-source custody or verification.

## Positive observations

- Backend/frontend public naming is now consistent: `segment_id` is public and `source_record_id` is persistence-only.
- Provenance includes typed `z_handling`, source quality, reference-only warning, CRS, processing, and uncertainty.
- Importer uses secure XML parsing, SHA-256 verification, transactional session scope, deterministic identity, and no topology reconstruction.
- API validates persisted geometry, bounds bbox input, applies the 5,000-feature cap, and distinguishes storage-empty from in-view misses.
- MapView removes stale stormwater sources/layers and filters synthetic edges to positive visits.

## Review verdict

**PASS:** CR-001 through CR-004 are resolved. Backend importer tests, frontend tests, build, and targeted Ruff checks pass. Official-source/PostGIS verification was not run in this review and is not represented as completed. No implementation files were edited during review.
