# Spec Delta

## Purpose

Provide official Taipei administrative district geometry as a provenance-preserving geographic reference layer, without representing it as rodent or infrastructure evidence.

## ADDED Requirements

### Requirement: Verified source import

The system MUST provide one documented command that imports the documented Taipei district boundary candidate from its source archive, verifies the archive hash, validates a non-ambiguous source CRS of EPSG:3826 with explicit axis order, validates finite non-empty Polygon or MultiPolygon geometry before and after transformation to EPSG:4326, enforces the documented source/target coordinate envelopes, and records a complete immutable provenance object. The provenance object MUST use the exact version-1 typed shape defined in design.md. Administrative records MUST carry `data_class=ADMINISTRATIVE_REFERENCE` and MUST NOT be represented as biological `OBSERVED`, `INFERRED`, or `SIMULATED`; this resource uses epistemic `classification=UNVERIFIED` because post-2022 currentness is unresolved.

#### Scenario: Valid source archive

- **WHEN** the documented importer receives the expected source archive
- **THEN** it validates the archive/hash and source CRS as EPSG:3826, accepts only finite non-empty Polygon or MultiPolygon records with valid geometry within the documented source and transformed envelopes, transforms them to EPSG:4326 without axis reversal, and persists NFC-normalized `CPID` identifiers and UTF-8 NFC-normalized `TNAME` names with the exact complete provenance object

#### Scenario: Invalid source

- **WHEN** the source archive is missing required files, has a missing/ambiguous/unsupported CRS, wrong axis order, coordinates outside either documented envelope, non-finite or invalid geometry, unsupported dimensionality/type, invalid archive hash, or lacks a non-empty unique normalized `CPID`/`TNAME`
- **THEN** the importer fails with a meaningful error and does not partially commit invalid records; it MUST NOT silently repair geometry

### Requirement: Idempotent district persistence

Repeated imports of the same source version and archive hash MUST transactionally upsert the same district records without creating duplicates, while preserving existing unrelated spatial records. A changed hash for an existing source version MUST fail closed and require a new source version; an omitted identifier MUST fail and roll back rather than silently delete an existing row. Imports are archive-only so extracted files cannot bypass source identity.

#### Scenario: Repeat import

- **WHEN** the importer is run twice against the same source version and identifiers
- **THEN** the second run produces the same district key set and no duplicate district records; changed content with the same hash is transactionally updated, a changed hash fails closed, and omitted records roll back

### Requirement: Boundary GeoJSON contract

The API MUST expose imported administrative districts as a valid GeoJSON FeatureCollection in EPSG:4326. The response MUST include `data_state` (`empty` or `available`), `data_class=ADMINISTRATIVE_REFERENCE`, and one complete version-1 provenance object at the top level when available; feature properties MUST preserve normalized district identifier/name, `classification=UNVERIFIED`, `data_class`, and source/version/hash references without duplicating the full provenance object. When no districts have been imported, it MUST return HTTP 200 with `data_state=empty` and no features; storage or serialization failure MUST be a non-2xx error and MUST NOT be disguised as empty data or fallback geometry.

#### Scenario: Imported data available

- **WHEN** a client requests the district-boundary endpoint after a successful import
- **THEN** the response is a FeatureCollection whose features contain valid EPSG:4326 Polygon or MultiPolygon geometry, stable district identifiers/names, and source metadata

#### Scenario: No imported data

- **WHEN** a client requests the district-boundary endpoint before import
- **THEN** the API returns HTTP 200 with an empty FeatureCollection and an explicit unavailable/empty state, without synthetic or fallback administrative geometry

### Requirement: Dashboard boundary visualization

The dashboard MUST display the API's imported administrative boundary FeatureCollection as a distinct administrative-reference layer with a visibility toggle, loading/empty/error states, and district name/source inspection on click. It MUST preserve existing simulation interactions and MUST NOT label administrative boundaries as rodent observations or simulated movement.

#### Scenario: Boundary layer loaded

- **WHEN** the boundary endpoint returns imported features and the user enables the layer after map style load
- **THEN** MapLibre renders the actual returned polygons, and keyboard-accessible selection exposes the district name, `ADMINISTRATIVE_REFERENCE` data class, currentness limitation, and source

#### Scenario: Boundary endpoint unavailable or empty

- **WHEN** the boundary endpoint is loading, fails, or returns `data_state=empty`
- **THEN** the dashboard communicates the corresponding loading/error/empty state, removes stale boundary source/layers, and renders no fabricated polygon; the synthetic simulation layer remains independent
