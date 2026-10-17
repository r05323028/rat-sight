# Design

## Exact fixture contract

The only permitted input for this change is the committed synthetic fixture
`services/api/tests/fixtures/rodent_reports/synthetic_reports.csv`. It has dataset ID
`00000000-0000-4000-8000-000000000002`, resource version `2026-10-17T00:00:00Z`, and a
recorded SHA-256 manifest in `services/api/tests/fixtures/rodent_reports/README.md`.
The importer pins all three values and rejects other source identities by default; no
real report download or source override flag exists.

The CSV has exactly these columns and no others:
`source_record_id`, `report_type`, `reported_at`, `longitude`, `latitude`,
`location_precision`, `review_status`, `municipal_status`, `action_status`.
Allowed values are: `report_type` = `sighting_report | nuisance_report | service_request | unknown`;
`location_precision` = `synthetic_point | coarse_grid_100m | coarse_grid_1km | unknown`;
`review_status` = `unreviewed | platform_moderated | municipal_reviewed | unknown`;
`municipal_status` = `not_assessed | confirmed_by_authority | rejected | unknown`;
`action_status` = `none_reported | inspection | treatment | unknown`.
Fixture rows use `location_precision=synthetic_point`, `review_status=unreviewed`,
`municipal_status=not_assessed`, and `action_status=none_reported`; these values are
not claims about a real reporting system.

`RodentReportProvenanceV1` is an immutable top-level Pydantic envelope with exactly:
`schema_version` literal `1`, `source_kind` literal `synthetic_fixture`, `dataset_id` UUID,
`resource_version` RFC3339 UTC timestamp, `retrieved_at` RFC3339 UTC timestamp,
`content_sha256` lowercase 64-hex string, `license` non-empty synthetic-fixture notice,
`attribution` non-empty RatSight fixture attribution, `source_crs` and `target_crs` literal
`EPSG:4326`, `processing` (`tool`, `tool_version`, non-empty `steps`), `synthetic` literal
`true`, and `uncertainty` (`currentness`, `note`). It is owned by the backend, serialized
once at the top level, and feature properties repeat only schema/dataset/version/hash
references. `data_class=RODENT_REPORT` and `classification=SIMULATED` are mandatory.

The serialized response is a GeoJSON `FeatureCollection` envelope with exactly these
keys: `type=FeatureCollection`, `data_state`, `data_class`, `classification`, `provenance`,
`feature_count`, `bbox` (normalized four-number EPSG:4326 array or `null`),
`reported_from` (normalized RFC3339 UTC string or `null`), `reported_to` (normalized
RFC3339 UTC string or `null`), `truncated`, and `features` (always an array). Storage-empty
has zero features and `bbox=null`; a successful filtered miss has `data_state=available`,
zero features, and echoes normalized filters. Each feature has exactly `type=Feature`,
`id=report_id`, 2D Point geometry `[longitude, latitude]`, and the allowlisted properties;
longitude/latitude are not duplicated as properties. `report_id` maps the normalized
`source_record_id`. Required source fields are non-null; empty lexical values are rejected,
not converted to null.

Feature properties are exactly these public keys: `report_id`, `source`, `report_type`,
`reported_at`, `location_precision`, `review_status`, `municipal_status`, `action_status`,
`data_class`, `classification`, `provenance_schema_version`, `dataset_id`,
`resource_version`, and `content_sha256`. `source` is the literal `synthetic_fixture`.
Importer-only fields `source_record_id`, `longitude`, and `latitude` are never public
properties; the latter two occur only in geometry. Unknown input columns and forbidden fields
(name, phone, email, photo, address, free text, exact-source payloads) are rejected and
never persisted or serialized. Coordinates are synthetic WGS84 points; no real precision
or personal location is disclosed. Future authorized data would require a new approved
contract and default `UNVERIFIED`; it cannot reuse this fixture provenance.

## Import and persistence

The local CSV fixture importer validates the exact header, UTF-8 CSV, unique non-empty
source IDs, RFC3339 UTC timestamps, finite longitude/latitude within EPSG:4326 ranges,
allowed enums, and content hash before a transaction. Invalid records fail closed before
writes. Persistence is additive and idempotent by `(dataset_id, resource_version,
source_record_id)` with content identity; changed or omitted records fail closed.

## API and UI

`GET /api/v1/rodent-reports` accepts optional `bbox=minX,minY,maxX,maxY` with exactly four
finite EPSG:4326 numbers, longitude/latitude ranges, ordered bounds, and width/height no
larger than 0.30 degrees; optional `reported_from` and `reported_to` are RFC3339 UTC,
normalized to `Z`, inclusive, and require `from <= to`. Invalid input returns HTTP 422;
storage failure is non-2xx. Results have deterministic `reported_at, report_id` ordering,
cap at 5,000 with `truncated`, echo normalized filters, and distinguish storage-empty
(`data_state=empty`) from in-filter empty (`available`, zero features).

The dashboard requests the viewport and an optional UTC `datetime-local` range. Each
control value is interpreted as UTC and converted to an RFC3339 `Z` query value at minute
precision; both controls default empty (all fixture times), not to a fabricated date window.
Viewport changes debounce at 250 ms. It shows exact loading/storage-empty/in-filter-empty/error/capped wording,
removes stale points, and exposes only the allowlisted fields plus provenance. It labels
reports `RODENT_REPORT` / `SIMULATED` and states they are synthetic report-shaped fixtures,
not verified observations, prevalence, population, movement, or risk. No heatmap,
clustering, score, graph edge, or simulation input is added.
