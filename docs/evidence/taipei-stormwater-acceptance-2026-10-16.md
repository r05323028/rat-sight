# Taipei Stormwater Official Acceptance

**Status: READY FOR HUMAN REVIEW**

**Evidence ID:** `EVID-TPE-STORMWATER-ACCEPTANCE-2026-10-16`

**Source evidence:** `EVID-TPE-STORMWATER-NETWORK-2026-10-16`

## Official source

- Dataset: `97b82d58-faba-4ee4-9488-dd5d04a79efd`
- Resource: `5240223d-5187-454e-b323-63443a195639`
- Resource version: `2026-02-23T17:10:41Z`
- Download URL: `https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=5240223d-5187-454e-b323-63443a195639`
- SHA-256: `5d2ea04f7d032d21b07066310e80eb64a34ce8916b4a0c786b10948aeb4e10e4`
- File: XML 1.0, UTF-8, 25,086,504 bytes; raw bytes remain outside Git.

## Source validation — VERIFIED

The production importer inspected the downloaded official bytes and found 19,747 records. All records had unique stable source identifiers, declared `EPSG:3826`, homogeneous 3D LineStrings, finite valid horizontal geometry, and were transformed to 2D `EPSG:4326` with `z_handling=dropped`. Source-quality counts were:

- missing pipe number: 20
- duplicate pipe-number values: 310
- missing start endpoint: 992
- missing end endpoint: 991
- missing notes: 17,950

These publisher attributes were retained; no topology, connectivity, traversability, rodent, or risk claim was inferred.

## Isolated import — VERIFIED

A disposable PostGIS stack was migrated `0001 → 0003` and the production importer was run twice. The first import inserted 19,747 records; the second inserted 0 and reported 19,747 unchanged. Post-import SQL confirmed 19,747 rows, 19,747 distinct source identifiers, 19,747 persistence keys, and geometry SRID 4326. No developer database, volume, or service was used.

Approximate wall-clock timings on the verification host:

- inspect/parse/validate/transform: 60.15 s
- first parse/transform/persist: 86.86 s
- idempotent re-import: 61.37 s

These are acceptance measurements, not benchmark claims. The dominant measured work is source XML parsing and coordinate transformation; no speculative optimization was made.

## FastAPI — VERIFIED

Against the isolated official database:

| Request | Status | Features | Truncated | Size | Time |
|---|---:|---:|---|---:|---:|
| no bbox | 200 | 5,000 | true | 4,401,424 bytes | 0.423 s |
| `121.50,24.98,121.63,25.09` | 200 | 5,000 | true | 4,455,658 bytes | 0.384 s |
| `120.0,24.0,120.1,24.1` | 200 | 0 | false | 1,943 bytes | 0.025 s |
| invalid >0.30° bbox | 422 | — | — | — | — |

Responses carried the official dataset/resource/hash provenance, `INFRASTRUCTURE_REFERENCE`, `UNVERIFIED`, and 2D `LineString` geometry. No fabricated geometry was observed. The broad real-data response naturally exercised the 5,000-feature cap.

## Next.js / MapLibre — VERIFIED

A focused Playwright run used the official imported database, live FastAPI, and live Next.js process. It loaded the dashboard, received real stormwater API features, enabled the stormwater layer, observed the reference warning and connectivity limitation, selected the first actual pipeline, and inspected its real segment ID and `INFRASTRUCTURE_REFERENCE` details. The MapLibre basemap style was stubbed only as in the existing smoke test; the application API was not intercepted.

The official response returned up to 5,000 features (4.4 MB). The dashboard now keeps map-based selection for all returned features while limiting the auxiliary keyboard list to the first 100, with an explicit notice. The focused browser run completed in 2.8 s; no additional rendering refactor was introduced.

Administrative boundaries and synthetic simulation remain separate. Synthetic edges continue to render only when `visits > 0`.

## Correctness and documentation stabilization — VERIFIED

- Removed the duplicate placeholder `Stormwater networks` presentation entry while retaining the actual `Stormwater pipelines` layer and backend catalog contract.
- Updated dashboard boundary language to distinguish infrastructure reference data from unavailable rodent observations.
- Updated `README.md`, `docs/infrastructure/data-sources.md`, `docs/infrastructure/stormwater-pipelines-import.md`, and `docs/architecture/overview.md` with the verified source and limitations.

## Checks

- Independent stabilization review: **PASS**, recorded in `openspec/changes/integrate-taipei-stormwater-network/verification/stabilization-review.md`.
- Focused independent acceptance QA: **CLEAR**, with addendum recorded in `openspec/changes/archive/2026-10-17-integrate-taipei-stormwater-network/verification/qa.md`.
- `uv run pytest -q`: **117 passed** after the focused UI-only stabilization; stormwater importer/API tests remained green.
- Frontend unit tests: **28 passed**.
- Frontend typecheck, lint, format, and build: **PASS**.
- `make geospatial-smoke`: **4/4** real-API smoke specs previously passed.
- Official district verification: **PASS**, isolated and cleaned.
- Official stormwater acceptance: **PASS**, isolated and cleaned.

## Archive decision status

The repository currently contains the archived change at `openspec/changes/archive/2026-10-17-integrate-taipei-stormwater-network/` in baseline commit `c189b55f212a9b3fc2edf810d0442becb81a5005`. Git history shows commit `c189b55` added the archive, but the inspected repository contains no explicit project-owner approval reference tied to that archive operation. The workflow documentation requires quality-gate PASS, then explicit project-owner acceptance, then archive. Whether such approval exists outside this repository is **UNVERIFIED**. This acceptance task does not unarchive, re-archive, or modify historical records.

## Remaining limitations and recommendation

- Currentness, engineering completeness, and physical connectivity remain `UNVERIFIED` per publisher/reference scope.
- The 5,000-feature API response is large; the measured 0.38–0.42 s API timings and focused 3.4 s browser run supported the minimal 100-item auxiliary list cap. Map rendering remains bounded by the API cap.
- No rodent observations, movement claims, risk scores, or biological conclusions are introduced.

**Recommendation:** accept the official stormwater integration for this focused reference-data scope only after project-owner review of this report and the archive-authorization uncertainty. Do not treat acceptance as scientific validation or as authorization for further archive/push operations.
