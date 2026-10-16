# Stormwater Network Specification

## Purpose

Provide a provenance-preserving Taipei stormwater infrastructure reference layer without treating infrastructure geometry as rodent evidence or physical connectivity.

## Requirements

### Requirement: Verified stormwater source import

The system MUST provide one documented local-source-file-only command (with no live download) for Candidate B dataset `97b82d58-faba-4ee4-9488-dd5d04a79efd`, resource `5240223d-5187-454e-b323-63443a195639`, resource version `2026-02-23T17:10:41`, and archive SHA-256 `5d2ea04f7d032d21b07066310e80eb64a34ce8916b4a0c786b10948aeb4e10e4`. It MUST verify the expected source identity and SHA-256, require the declared EPSG:3826 CRS, parse 3D GML LineString records, reject mixed/unsupported dimensions, validate finite non-empty valid horizontal geometry, drop unresolved Z values to 2D EPSG:4326 while recording the vertical-datum limitation, preserve nullable source attributes, record typed `StormwaterProvenanceV1`, and fail closed without partial writes. Missing or duplicate `管線編號` values MUST be retained honestly as attributes and MUST NOT be used to infer connectivity.

#### Scenario: Valid stormwater source

- **WHEN** the importer receives the expected local Candidate B resource
- **THEN** it validates identity/hash/CRS, imports valid LineStrings transactionally as EPSG:4326 infrastructure reference records, and records source/version/license/processing/uncertainty provenance

#### Scenario: Invalid or ambiguous source

- **WHEN** the source hash, CRS, XML structure, geometry, or required source identity is invalid
- **THEN** the importer fails with a useful error and leaves no partial stormwater import; it does not repair geometry or invent identifiers

### Requirement: Idempotent stormwater persistence

Repeated imports of the same dataset, resource version, archive hash, and source records MUST not create duplicate rows or alter unrelated tables. Conflicting content for an existing source version MUST fail closed or update only the same deterministic source record under an explicit content identity; omitted records MUST not silently delete prior records.

#### Scenario: Repeat import

- **WHEN** the same verified resource is imported twice
- **THEN** the second import is unchanged/idempotent and the persisted source identity set remains stable

### Requirement: Stormwater GeoJSON API

The API MUST expose versioned stormwater pipeline GeoJSON in EPSG:4326 with `data_state`, `data_class=INFRASTRUCTURE_REFERENCE`, and a top-level immutable `StormwaterProvenanceV1` exactly shaped as: `{schema_version: "1", source_url: http(s) URI, download_url: http(s) URI, dataset_id: UUID string, resource_id: UUID string, resource_version: RFC3339 UTC string, retrieved_at: RFC3339 UTC string, archive_sha256: 64 lowercase-hex string, license: non-empty string, attribution: non-empty string, source_crs: "EPSG:3826", target_crs: "EPSG:4326", z_handling: "dropped" | "retained" | "not_present", processing: {tool: non-empty string, tool_version: non-empty string, steps: non-empty string array}, source_quality: {reference_only: boolean, missing_pipe_number_count: non-negative integer, duplicate_pipe_number_value_count: non-negative integer, missing_start_endpoint_count: non-negative integer, missing_end_endpoint_count: non-negative integer, missing_notes_count: non-negative integer}, uncertainty: {currentness: non-empty string, note: non-empty string}}`. It MUST preserve source identity/hash/license/CRS/processing/currentness and reference-only/data-quality limitations, and feature properties MUST contain the defined source-attribute allowlist plus the required provenance references `provenance_schema_version`, `dataset_id`, `resource_version`, and `archive_sha256`, plus `data_class=INFRASTRUCTURE_REFERENCE` and `classification=UNVERIFIED`. `segment_id` is the opaque API representation of the normalized unique `識別碼` persisted as `source_record_id`; every source record MUST have exactly one non-empty unique value and missing/duplicate values MUST fail the import. `管線編號`, endpoint IDs, dimensions, dates, status, and notes are nullable publisher attributes, not topology. The exact property allowlist is `segment_id`, `category_code`, `pipe_number`, `start_node_id`, `end_node_id`, `managing_unit`, `work_category`, `installation_date`, `dimension_unit`, `diameter_width`, `diameter_height`, `conduit_count`, `material`, `start_burial_depth`, `end_burial_depth`, `length`, `pipe_type`, `use_status`, `data_status`, and `notes`; every field except `segment_id` is an optional nullable string preserving source lexical values, and omitted source values are rendered as `Unavailable`. It MUST return an explicit empty response before import, a non-2xx storage failure, and a validated bounded `bbox` result when supplied. Bbox values MUST be four finite EPSG:4326 numbers in `minX,minY,maxX,maxY` order, within longitude/latitude ranges, ordered min≤max, with width and height no greater than 0.30 degrees; invalid input is HTTP 422. Responses MUST include `feature_count`, echo the normalized bbox when supplied, and cap results at 5,000 with `truncated=true` when capped. The endpoint MUST not expose inferred topology or rodent claims.

#### Scenario: Available bounded data

- **WHEN** a client requests the endpoint after import, optionally with a valid EPSG:4326 bbox
- **THEN** it receives only matching valid LineString features with source metadata and provenance

#### Scenario: Empty or invalid query

- **WHEN** no selected-version records exist or bbox syntax/range is invalid
- **THEN** the API returns an explicit empty state or a client error respectively, without fallback geometry

### Requirement: Stormwater dashboard inspection

The dashboard MUST request the current MapLibre viewport bbox on initial map load and on debounced `moveend` events, provide an independent stormwater layer toggle, loading/empty/error states, distinct infrastructure styling, pipeline selection, meaningful allowlisted source-attribute inspection with null values shown as unavailable, attribution, resource-version/currentness display, and no coupling to administrative or synthetic simulation layers. It MUST distinguish storage-empty (`No pipelines imported`) from an in-view miss (`No pipelines in view`) and a capped response (`showing partial data, zoom in`); stale stormwater source/layers MUST be removed when the response is empty or unavailable.

#### Scenario: Pipeline available

- **WHEN** the stormwater endpoint returns features and the user enables the layer
- **THEN** MapLibre renders the returned lines, and selecting a line exposes its source identity/attributes, infrastructure classification, and provenance

#### Scenario: Pipeline unavailable

- **WHEN** the endpoint is loading, empty, or unavailable
- **THEN** the dashboard communicates that state and renders no fabricated line or simulated movement

### Requirement: Existing layer integrity

Synthetic map traversal visualization MUST include only simulation edges with positive visits, and the existing administrative boundary layer MUST remain independently importable, queryable, selectable, and verifiable against its documented official archive in an isolated one-time check.

#### Scenario: Unvisited simulation edge

- **WHEN** a simulation response contains an edge with zero visits
- **THEN** that edge is not rendered as a simulated traversal

#### Scenario: Official administrative check

- **WHEN** `scripts/verify_official_districts.sh` downloads the documented official district archive into a temporary isolated verification environment
- **THEN** its hash, expected district identity set, PostGIS persistence, API GeoJSON, and dashboard inspection path are checked, the durable result is recorded in the OpenSpec QA artifact, and no regular test fixture or shared developer data is changed
