# Spec Delta

## ADDED Requirements

### Requirement: Rodent report source boundary

The system MUST document candidate source ownership, access, licensing, semantics, spatial and temporal coverage, privacy, and quality limitations before real report ingestion. Until a source is authorized and its privacy/reuse contract is verified, the system MUST use only local synthetic fixtures and MUST NOT download, store, or redistribute real citizen-report records.

#### Scenario: Unverified source

- **WHEN** a candidate lacks written reuse/privacy authorization or a verified schema and CRS
- **THEN** it remains `UNVERIFIED`, no real records are imported, and the limitation is visible in evidence and acceptance documentation

### Requirement: Validated rodent report import

The system MUST provide a documented local-file-only importer for the pinned synthetic fixture `services/api/tests/fixtures/rodent_reports/synthetic_reports.csv`, with dataset ID `00000000-0000-4000-8000-000000000002`, resource version `2026-10-26T17:22:26Z`, and manifest SHA-256. It MUST reject any other identity/hash and validate the exact CSV header, unique source identity, RFC3339 UTC timestamps, finite EPSG:4326 point coordinates, bounded report/status/precision enums, and the immutable typed `RodentReportProvenanceV1` envelope before any write. Fixture records MUST be labeled `data_class=RODENT_REPORT` and `classification=SIMULATED`; invalid, changed, or forbidden-field content MUST fail closed without partial writes.

#### Scenario: Valid synthetic fixture

- **WHEN** the importer receives the documented fixture with a matching source identity and content hash
- **THEN** it persists deterministic point reports transactionally and preserves synthetic provenance

### Requirement: Bounded rodent report API

The API MUST expose a versioned GeoJSON `FeatureCollection` whose exact envelope includes `type`, `data_state`, `data_class`, `classification`, immutable `RodentReportProvenanceV1`, `feature_count`, `bbox` (four-number array or null), `reported_from` (RFC3339 UTC string or null), `reported_to` (RFC3339 UTC string or null), `truncated`, and `features`. Each feature MUST have `type=Feature`, `id=report_id`, 2D Point geometry, and exactly these public properties: `report_id`, `source`, `report_type`, `reported_at`, `location_precision`, `review_status`, `municipal_status`, `action_status`, `data_class`, `classification`, `provenance_schema_version`, `dataset_id`, `resource_version`, and `content_sha256`. Importer-only `source_record_id`, `longitude`, and `latitude` MUST NOT be public properties; longitude/latitude MUST NOT be duplicated outside geometry. It MUST use `data_class=RODENT_REPORT`, `classification=SIMULATED`, validated bounded EPSG:4326 bbox, inclusive RFC3339 UTC temporal filtering, deterministic `reported_at,report_id` ordering, and a maximum of 5,000 features. Bbox values MUST be four finite numbers in range/order with width and height no greater than 0.30 degrees; invalid bbox/time/range input is HTTP 422 and storage failure is non-2xx. Responses MUST echo normalized filters, distinguish storage-empty from in-filter empty, and MUST NOT expose forbidden personal fields or infer biological meaning.

#### Scenario: Spatial and temporal query

- **WHEN** a client supplies a valid bbox and optional UTC time range
- **THEN** it receives only matching point reports with report semantics, classification, and provenance

### Requirement: Rodent report dashboard inspection

The dashboard MUST provide an independent Rodent reports layer toggle, current viewport querying, optional UTC `datetime-local` temporal filtering converted at minute precision to RFC3339 `Z` values (empty by default), loading/storage-empty/in-filter-empty/error/capped states, point selection, allowlisted report details, typed provenance, and visible `RODENT_REPORT` / `SIMULATED` wording that reports are not verified observations, prevalence, population, movement, or risk evidence. It MUST remove stale points when data is empty or unavailable and MUST remain independent of administrative, stormwater, and simulation layers.

#### Scenario: Select synthetic report

- **WHEN** the fixture-backed API returns reports and the user enables the layer
- **THEN** the dashboard renders returned points and selection exposes the report type, time, status, synthetic classification, and provenance

### Requirement: Existing layer integrity

Administrative boundaries, stormwater reference data, and synthetic simulation MUST remain independently queryable and renderable. Rodent reports MUST NOT create simulation edges, infrastructure connectivity, heatmaps, risk scores, or biological claims.

#### Scenario: Existing layers remain independent

- **WHEN** rodent reports are imported or queried
- **THEN** administrative, stormwater, and simulation responses remain unchanged and no report feature is used as a simulation or infrastructure edge.
