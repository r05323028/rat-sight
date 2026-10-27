# Design

## Evidence and authorization status

- Source: public citizen-report export `https://ratdar.taipei/`; observed export SHA-256 `eae7182b7f1cb57a73c1c074e732a8d5780da0cbdc7c481c3972ec7f3c23c24b`, 1,435 parsed reports, 2026-05-01 → 2026-10-25.
- Status: `AUTHORIZATION=ASSERTED_BY_PROJECT_OWNER`, `EVIDENCE=ABSENT`, `REUSE=UNVERIFIED`. Recorded in `docs/evidence/ratdar-reuse-claim-2026-10-26.md`.
- Decision: the project owner directed on 2026-10-26 that a de-identified aggregate be built and shown, after the reuse and privacy blockers were disclosed. That is an override, not a resolution; the change documents it and keeps the limits visible in API and UI.

## Aggregation rules

- Grid: fixed 250 m cells anchored at the equator/prime meridian. `LAT_STEP = 250 / 111320.0` degrees; the longitude step uses the cell's centre latitude, so cell height is constant and width approximates 250 m. Cell id is `g250m:{lat_index}:{lon_index}`.
- Buckets: `(cell, month, report_type)` where month is the export's wall-clock `YYYY-MM` string. The UTC offset of the export is unverified, so the assumption is carried verbatim in provenance (`month_timezone_assumption`).
- Report types: `鼠蹤 → sighting`, `毒餌 → bait_station`, anything else → `other`, matching the observed export vocabulary without inventing categories.
- Suppression: a cell-month needs ≥3 reports and every published `(cell, month, report_type)` row needs ≥3. Both are enforced in the importer and by database `CHECK (report_count >= 3)`. Suppressed records are counted, not published: `suppressed_records`, `suppressed_cells`.
- Why 250 m: measured survival on the observed export was 100 m → 29 published rows across 28 cells covering 95 reports (most density lost), 250 m → 91 published rows across 91 cells covering 319 reports, 500 m → 178 rows but coarse enough to blur the districts the layer is meant to show. 250 m keeps the layer readable while still suppressing most small groups.
- Dropped before write: `地點` (place name), `說明` (free text), `照片網址` (photo URL). Exact coordinates are used transiently for cell assignment and are never persisted; the API exposes cell polygons only.

## Persistence

- Table `citizen_report_cells`: `dataset_id`, `resource_version`, `cell_id`, `month`, `report_type`, `report_count`, `data_class`, `classification`, `attribution`, plus a 2D `POLYGON`/`MULTIPOLYGON` geometry in `EPSG:4326`.
- Unique key `uq_citizen_report_cells_key` on `(dataset_id, resource_version, cell_id, month, report_type)` makes re-imports idempotent via `ON CONFLICT DO NOTHING`.
- `CHECK` constraints pin `data_class='CITIZEN_REPORT_AGGREGATE'`, `classification='UNVERIFIED'`, and `report_count >= 3`, so a future writer cannot publish a finer classification or an unsuppressed count by accident.
- Trigger `citizen_report_cells_immutable` blocks `UPDATE`/`DELETE`, matching the append-only pattern used by rodent reports.
- GIST index on geometry and a `(resource_version, month)` index serve bbox and month filtering.

## API contract

- Route: `GET /api/v1/citizen-report-aggregates?bbox=&months=&report_type=`.
- Only the latest `resource_version` for `DATASET_ID` is served, so a re-import swaps the whole artifact atomically rather than blending versions.
- `bbox` is four finite numbers in range and order with width/height ≤ 0.30 degrees; `months` is a comma list of `YYYY-MM`; invalid input is 422. Storage failure is non-2xx, empty storage is `data_state=empty` with `provenance=null`, and a filter miss is `data_state=empty` with provenance retained — the two are distinguishable.
- Envelope: `type`, `data_state`, `data_class`, `classification`, `notice`, `provenance`, `feature_count`, `bbox`, `truncated`, `features` (cap 5,000).
- Feature properties are exactly `cell_id`, `month`, `report_type`, `count`, `data_class`, `classification`, `attribution`. No place name, no free text, no photo URL, no exact coordinate.
- `CitizenReportProvenanceV1` is frozen and carries `source_kind=public_citizen_report_export`, `dataset_id`, `resource_version`, `retrieved_at`, `content_sha256`, `source_url`, `license`, `attribution`, source/target CRS, `processing`, `aggregation` (cell size, month-timezone assumption, suppression minimum, dropped fields), `counts`, `synthetic=false`, and `uncertainty`.

## Dashboard

- Independent layer with its own toggle (no coupling to stormwater or simulation rendering), rendered as a translucent 250 m fill plus outline beneath simulated paths. Explicit cell selection may feed the separate origin resolver described by `citizen-report-driven-simulation-origins`; the layers never merge semantics.
- Panel discloses: cell/report/month counts, `UNVERIFIED` badge, the suppression rule, exactly which fields were dropped, attribution, source URL, licence text, resource version, content SHA-256, parsed/used/suppressed counts, the month-timezone assumption, and currentness.
- The empty state says no aggregate is imported instead of substituting another layer; the error state never renders a zero count.
- Copy states plainly that the layer is not a rodent observation, prevalence, population, movement, or risk estimate. Counts are not simulation inputs: a separately approved origin contract may use one selected cell only to resolve a single strictly in-cell graph node, never walker counts or transition weights.

## Reversibility

Dropping the table and removing the layer reverts the publication completely. Only the separate origin resolver reads a selected cell; it fails closed when no single graph node lies strictly inside the cell.

## Decision: no report-derived origins (2026-10-26)

Orchestration verdict, recorded after a read-only readiness assessment (`/tmp/citizen-origin-readiness-2026-10-26.md`):

- The aggregate stays display-only and independent of every other layer. Simulation origins remain exact, validated pinned-OSM node ids only.
- No `origin-candidates` endpoint, no cell-to-network mapping, no aggregate-derived eligibility, and no aggregate as simulation input. A scoped synthetic-only origin contract/resolver is tracked separately and does not change this boundary.
- Blocked pending: owner/source terms for the export (grantor identity, licence, retention), independent privacy review, scientific approval of any report-to-presence inference, and a spec change. The measured join also argues against it: 0 of 91 published cells contain a pinned-OSM node and 1 lies within 250 m, so a report-derived origin would rest on a single cell at the suppression floor.
