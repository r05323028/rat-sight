# Stormwater pipeline import command

This document describes the single, local-file-only command that imports the
documented Taipei stormwater utility XML into PostGIS and the behavior an
operator should expect. It never downloads data, reconstructs topology, or
represents infrastructure geometry as rodent evidence.

## Data classification

- `data_class = INFRASTRUCTURE_REFERENCE`
- epistemic `classification = UNVERIFIED` (legal/engineering currency and
  completeness are not established)
- Evidence ID: `EVID-TPE-STORMWATER-NETWORK-2026-10-16`
  (`docs/evidence/taipei-stormwater-network-2026-10-16.md`)

Endpoint IDs (`start_node_id`, `end_node_id`) are **publisher attributes only**.
They are not verified physical connectivity, traversability, topology, movement
weights, or risk. Administrative and simulation layers remain independent.

## Source identity (Candidate B)

- Dataset: `97b82d58-faba-4ee4-9488-dd5d04a79efd`
- Resource: `5240223d-5187-454e-b323-63443a195639`
- Resource version: `2026-02-23T17:10:41Z`
- Source SHA-256: `5d2ea04f7d032d21b07066310e80eb64a34ce8916b4a0c786b10948aeb4e10e4`
- Geometry: homogeneous 3D GML `LineString`, `srsName="EPSG:3826"`,
  `srsDimension="3"`; the undocumented third coordinate is dropped and output is
  2D EPSG:4326.

Raw official XML remains outside Git (see `data/raw/README.md`).

## Prerequisites

- PostGIS running (`make db-up`) and migrated (`make migrate`), which additively
  creates `stormwater_pipelines`.
- The licensed source XML stored outside the repository.

## Command

```sh
python -m ratsight_api.importers.stormwater_pipelines \
  --source /path/to/A8040201_11502.xml \
  --archive-sha256 5d2ea04f7d032d21b07066310e80eb64a34ce8916b4a0c786b10948aeb4e10e4 \
  --retrieved-at 2026-10-16T00:00:00Z --inspect-only
```

Omit `--inspect-only` to persist. The Make target is:

```sh
make import-stormwater ARGS="--source ... --archive-sha256 ... --retrieved-at ..."
```

The CLI pins the documented Candidate B dataset, resource, version, and SHA-256.
For deterministic non-official fixtures only, pass `--allow-nonofficial-source`; this
flag is not a bypass for production official acceptance.

## Behavior

- **Local-file-only.** The command verifies the file SHA-256 against
  `--archive-sha256`; no live download occurs.
- **Fail-closed validation.** A missing/empty `識別碼` (the stable key), a
  duplicate `識別碼`, a non-`EPSG:3826` `srsName`, a non-3D `srsDimension`, a
  non-homogeneous coordinate sequence, non-finite coordinates, fewer than two
  distinct points, or an invalid/empty LineString aborts the import with no
  partial writes. Geometry is never repaired and identifiers are never invented.
- **Secure parsing.** XML is parsed with `defusedxml` to avoid entity-expansion
  attacks before any record is accepted.
- **Identity.** Records are keyed by `(dataset_id, resource_version,
  source_record_id)`, where `source_record_id` is the normalized unique
  `識別碼`. `管線編號` and endpoint IDs are nullable attributes, never keys.
- **Idempotency.** Re-importing the same version and identical content is a
  no-op. A different archive hash for an existing version, a changed record set,
  or changed content fails closed and requires a new `--resource-version`.
  Imports run in one transaction.
- **Provenance.** Each row stores an immutable `StormwaterProvenanceV1`
  (source/download URLs, dataset/resource/version, retrieval time, hash, license,
  attribution, CRS pair, `z_handling`, processing, `source_quality` counts,
  reference-only and currentness uncertainty).

## Exit codes

| Code | Meaning |
| ---- | ------- |
| 0 | Success (import or inspection) |
| 2 | Source validation failed (hash, CRS, dimensions, geometry, identity) |
| 3 | Import conflict (changed hash, changed/omitted record set) |
| 4 | Storage unavailable |

## API behavior

`GET /api/v1/stormwater-pipelines` returns `application/geo+json`:

- `data_state = "empty"` with HTTP 200 and zero features when nothing has been
  imported; it never fabricates fallback geometry.
- `data_state = "available"` with HTTP 200, the latest version's features, one
  top-level `StormwaterProvenanceV1`, `feature_count`, the echoed `bbox`, and
  `truncated` when the 5,000-feature cap is exceeded.
- Optional `bbox=minX,minY,maxX,maxY` (EPSG:4326, width/height ≤ 0.30 degrees)
  filters server-side via the GiST-indexed geometry. An invalid bbox returns
  HTTP 422; a viewport with no matches still returns `available` with
  `feature_count = 0`.
- HTTP 503 when storage is unavailable; malformed persisted data is an explicit
  non-2xx error and is never disguised as empty data.
