# Administrative boundary import command

This document describes the single, archive-only command that imports the
documented Taipei administrative district boundary resource into PostGIS and the
behavior an operator should expect. It does not fetch data and it does not
create rodent or infrastructure evidence.

## Data classification

- `data_class = ADMINISTRATIVE_REFERENCE`
- epistemic `classification = UNVERIFIED` (the 2022-09-15 resource version's
  legal currency after that version is unresolved)
- Evidence ID: `EVID-TPE-DISTRICT-BOUNDARIES-2026-10-15`
  (`docs/evidence/taipei-district-boundaries-2026-10-15.md`)

Administrative reference geometry is never represented as `OBSERVED`,
`INFERRED`, or `SIMULATED` rodent or infrastructure data, and it is not
simulated movement.

## Prerequisites

- PostGIS is running (`make db-up`) for a real import.
- The migration is applied (`make migrate`), which additively creates
  `administrative_districts`.
- The licensed source archive is stored outside the repository (for example
  under a path referenced by `data/raw/README.md`). Raw data is never committed.

## Command

```sh
python -m ratsight_api.importers.administrative_districts \
  --archive /path/to/臺北市區界圖_20220915.zip \
  --archive-sha256 77bcc347b503b8ff8a43f7e1afaaedb18877a6222282587b145adaba69afd2d9 \
  --source-url https://data.taipei/api/dataset/1601ef3a-c253-4988-b047-943d9e786143/resource/d8b7eb29-136f-49fc-b14b-3489d3656122/download \
  --dataset-id 121199 \
  --resource-version 20220915 \
  --retrieved-at 2026-10-15T00:00:00Z \
  --license "政府資料開放授權條款-第1版" \
  --attribution "臺北市政府民政局"
```

The equivalent Make target is:

```sh
make import-districts ARGS="--archive ... --archive-sha256 ... --source-url ... \
  --dataset-id 121199 --resource-version 20220915 --retrieved-at 2026-10-15T00:00:00Z \
  --license '...' --attribution '...'"
```

Add `--inspect-only` to verify the archive, hash, CRS, geometry, and envelopes
without writing to PostGIS. This is the safe verification path and cannot import
without the archive hash.

## Behavior

- **Archive-only.** The command accepts the source archive, verifies its SHA-256
  against `--archive-sha256`, and reads the single shapefile inside it.
  Extracted files cannot bypass source identity. No live download occurs.
- **Fail-closed CRS/geometry.** A missing or ambiguous `.prj`, a CRS other than
  EPSG:3826, wrong axis order, unsupported geometry type/dimension, invalid or
  empty geometry, non-finite coordinates, out-of-envelope coordinates, or a
  missing/duplicate/non-normalized `CPID`/`TNAME` abort the import. Invalid
  geometry is never silently repaired.
- **Envelopes.** Source coordinates must fall inside the documented EPSG:3826
  envelope and transformed coordinates inside the EPSG:4326 envelope. These are
  axis/CRS sanity bounds, not an expected district count.
- **Idempotency.** Records are keyed by `(dataset_id, resource_version,
  district_id)`. Re-running the same version and archive hash updates changed
  rows and leaves unchanged rows alone. A different hash for an already-imported
  version fails closed and requires a new `--resource-version`. An import that
  omits a previously imported identifier fails and rolls back rather than
  deleting data. The whole import is one transaction.
- **Provenance.** Every row stores the immutable version-1 provenance object
  (source URL, dataset/resource version, retrieval time, archive hash, license,
  attribution, source/target CRS, processing, currentness/uncertainty). The API
  serializes one canonical copy at the top level of the response.

## Exit codes

| Code | Meaning |
| ---- | ------- |
| 0 | Success (import or inspection) |
| 2 | Source validation failed (hash, CRS, geometry, attributes, envelope) |
| 3 | Import conflict (changed hash for an existing version, or omitted identifier) |
| 4 | Storage unavailable |

## API behavior

`GET /api/v1/administrative-districts` returns `application/geo+json`:

- `data_state = "empty"` with HTTP 200 and zero features when nothing has been
  imported. It never fabricates fallback geometry.
- `data_state = "available"` with HTTP 200, the latest resource version's
  features, and one top-level provenance object when data is imported.
- HTTP 503 when storage is unavailable; a non-2xx error is never disguised as
  empty data.
