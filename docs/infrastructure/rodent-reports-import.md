# Rodent report import command (fixture-only)

This document describes the fixture-only local importer and API for synthetic
rodent-report points. It never downloads, stores, or redistributes real citizen
reports, and it has no source override.

## Data classification

- `data_class = RODENT_REPORT`
- epistemic `classification = SIMULATED`
- `source_kind = synthetic_fixture`

Synthetic report-shaped records are **not** observations, prevalence, population,
movement, disease risk, or intervention evidence. They are not linked to
simulation or infrastructure topology.

## Pinned fixture

- Path: `services/api/tests/fixtures/rodent_reports/synthetic_reports.csv`
- dataset ID: `00000000-0000-4000-8000-000000000002`
- resource version: `2026-10-26T17:22:26Z`
- content SHA-256: `b28305e75e02d88a0a18f5455ce2a8e26c6db47ab657e621cb3d63f39a84655d`
- records: 160 (`scripts/generate_synthetic_rodent_reports.py`, seed `20261026`)
- shape: coarse report-type/month/time-of-day aggregates only; no citizen record reproduced
- manifest: `services/api/tests/fixtures/rodent_reports/README.md`

Columns (exactly, in order): `source_record_id`, `report_type`, `reported_at`,
`longitude`, `latitude`, `location_precision`, `review_status`,
`municipal_status`, `action_status`.

Enums: `report_type` = `sighting_report | nuisance_report | service_request |
unknown`; `location_precision` = `synthetic_point | coarse_grid_100m |
coarse_grid_1km | unknown`; `review_status` = `unreviewed | platform_moderated |
municipal_reviewed | unknown`; `municipal_status` = `not_assessed |
confirmed_by_authority | rejected | unknown`; `action_status` = `none_reported |
inspection | treatment | unknown`.

## Command

```sh
make import-rodent-reports ARGS="--inspect-only"
make import-rodent-reports
```

The importer pins the fixture path, dataset, version, and SHA-256; there is no
`--source`/identity override. It never downloads a real source.

## Behavior

- **Fail-closed validation** before any write: exact header and column order,
  UTF-8, unique non-empty `source_record_id`, RFC3339 UTC timestamps, finite
  EPSG:4326 longitude/latitude, allowed enums, and pinned content hash. Unknown
  or forbidden columns (name, phone, email, photo, address, free text, source
  payloads) are rejected. Invalid, changed, or omitted records roll back.
- **Idempotent persistence** keyed by `(dataset_id, resource_version,
  source_record_id)` with per-record content identity; a changed record set or
  changed content fails closed. Imports run in one transaction.
- **Immutable after import.** Migration `0004_rodent_reports` (and the forward
  repair `0006_rodent_reports_immutability`) install the
  `rodent_reports_immutable` trigger, which blocks `UPDATE` and `DELETE`. Reset a
  fixture only by recreating a disposable database/volume; never by deleting
  rows. A new `--resource-version`/dataset identity is required to change data.
- **SIMULATED enforced.** The table CHECK requires `classification = 'SIMULATED'`
  and `data_class = 'RODENT_REPORT'`; the API validates each persisted row and
  returns an explicit non-2xx data-contract error on inconsistent stored values
  instead of relabeling them.
- **Typed provenance**: immutable `RodentReportProvenanceV1` with
  `source_kind=synthetic_fixture`, `synthetic=true`, pinned dataset/version/hash,
  license/attribution notices, CRS pair, processing steps, and uncertainty.

## API behavior

`GET /api/v1/rodent-reports` returns `application/geo+json`:

- `data_state = "empty"` with HTTP 200 when nothing has been imported.
- `data_state = "available"` with the latest fixture version's points, one
  top-level `RodentReportProvenanceV1`, `feature_count`, echoed `bbox` /
  `reported_from` / `reported_to`, and `truncated` at the 5,000 cap.
- Optional `bbox=minX,minY,maxX,maxY` (EPSG:4326, width/height ≤ 0.30) and
  inclusive RFC3339 UTC `reported_from`/`reported_to` with `from <= to`; invalid
  input returns HTTP 422.
- Deterministic `reported_at, report_id` ordering; a filter miss returns
  `available` with zero features and echoed filters; storage failure is 503 and
  malformed persisted data is 500.
- Feature properties expose only `report_id`, `source`, `report_type`,
  `reported_at`, `location_precision`, `review_status`, `municipal_status`,
  `action_status`, `data_class`, `classification`, and provenance references.
  `source_record_id`, `longitude`, and `latitude` are never public properties;
  coordinates appear only as 2D Point geometry.

Any future real report source requires data-owner authorization, written
license/reuse and privacy/retention terms, a verified schema/CRS, and human
public-health acceptance; it cannot reuse this fixture provenance or be labeled
`SIMULATED`.

## Smoke reset

`scripts/rodent_report_smoke.sh` resets the populated→empty scenario by
recreating its disposable compose volume, running migrations, and verifying the
immutability trigger is installed. `scripts/seed_rodent_report_smoke.py` never
deletes rows: with `SMOKE_EMPTY=1` it only verifies the disposable database is
freshly empty and exits non-zero otherwise. Production immutability and shared
developer data are never touched.
