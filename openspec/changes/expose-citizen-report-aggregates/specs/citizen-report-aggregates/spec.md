# Spec Delta

## ADDED Requirements

### Requirement: Citizen-report aggregate source boundary

The system MUST treat public citizen-report exports as personal data with unverified reuse status. It MUST NOT store, publish, or redistribute place names, free text, photo URLs, or exact report coordinates, and MUST NOT present citizen reports as observations, prevalence, population, movement, or risk evidence. Reuse authorization that is asserted without licence text, grantor identity, or retention terms MUST remain recorded as `REUSE=UNVERIFIED` even when a suppressed aggregate is published under an explicit owner override.

#### Scenario: Unverified reuse with an override

- **WHEN** an owner authorizes publication without supplying licence, grantor, or retention evidence
- **THEN** the evidence record keeps `AUTHORIZATION=ASSERTED_BY_PROJECT_OWNER`, `EVIDENCE=ABSENT`, `REUSE=UNVERIFIED`, the override is dated and attributed, and only suppressed aggregates are published

### Requirement: Spatial and categorical suppression

The importer MUST aggregate a public citizen-report export into fixed 250 m grid cells × wall-clock month × report type and MUST drop every `(cell, month, report_type)` row and every cell-month with fewer than 3 reports. It MUST NOT persist exact coordinates, place names, free text, or photo URLs, and MUST count suppressed records and suppressed groups in provenance. Invalid coordinates or timestamps MUST be counted as invalid rather than silently dropped, and an export with no surviving group MUST fail closed without a partial write.

#### Scenario: Small-cell suppression

- **WHEN** a cell-month contains 4 reports split 2/2 across two report types
- **THEN** no row is published for that cell-month, and the suppressed records and groups are recorded in provenance counts

### Requirement: Aggregate persistence

The system MUST store aggregates in `citizen_report_cells` with `data_class=CITIZEN_REPORT_AGGREGATE`, `classification=UNVERIFIED`, a 2D `EPSG:4326` cell polygon, and a unique key over `dataset_id, resource_version, cell_id, month, report_type`. Database constraints MUST reject any other data class, any other classification, and any count below the suppression minimum. Rows MUST be append-only, and re-importing the same artifact MUST be idempotent.

#### Scenario: Re-import the same export

- **WHEN** the importer runs twice on the same export
- **THEN** the second run adds no rows and the served artifact is unchanged

### Requirement: Bounded aggregate API

The API MUST expose `GET /api/v1/citizen-report-aggregates` as a GeoJSON `FeatureCollection` whose envelope includes `type`, `data_state`, `data_class`, `classification`, `notice`, `provenance`, `feature_count`, `bbox`, `truncated`, and `features`. Feature properties MUST be exactly `cell_id`, `month`, `report_type`, `count`, `data_class`, `classification`, and `attribution`. It MUST serve only the latest `resource_version` for the dataset, accept bounded `bbox` (width/height ≤ 0.30 degrees), `months` (`YYYY-MM`), and `report_type` filters, return HTTP 422 for invalid input and a non-2xx status for storage failure, distinguish storage-empty from filter-miss, and cap output at 5,000 features with `truncated` set when capped.

#### Scenario: Filter miss versus empty storage

- **WHEN** storage holds a versioned aggregate and the request filter matches nothing
- **THEN** the response is `data_state=empty` with provenance retained, distinguishing it from storage-empty responses that carry no provenance

### Requirement: Typed aggregate provenance

Every non-empty response MUST carry an immutable `CitizenReportProvenanceV1` with `source_kind=public_citizen_report_export`, `dataset_id`, `resource_version`, `retrieved_at`, `content_sha256`, `source_url`, `license`, `attribution`, source and target CRS, `processing` steps, `aggregation` metadata (cell size, month-timezone assumption, suppression minimum, dropped fields), `counts`, `synthetic=false`, and an uncertainty note. The licence field MUST state that reuse is unverified rather than implying a grant.

#### Scenario: Inspect provenance

- **WHEN** a client reads a non-empty aggregate response
- **THEN** provenance names the source URL, content hash, suppression rules, dropped fields, and the unverified-licence statement

### Requirement: Aggregate dashboard inspection

The dashboard MUST provide an independent citizen-report aggregate layer with its own toggle, viewport-bounded loading, and an `UNVERIFIED` badge. The panel MUST disclose published cell and report counts, the suppression rule, the dropped fields, attribution, source URL, licence status, resource version, content hash, and the month-timezone assumption, and MUST state that the layer is not an observation, prevalence, population, movement, or risk estimate and not a simulation input. Empty, loading, error, and unavailable states MUST NOT render a zero count or substitute another dataset.

#### Scenario: Toggle the aggregate layer

- **WHEN** the API returns aggregate cells and the user enables the layer
- **THEN** cells render as suppressed polygons and the panel shows counts, suppression disclosure, attribution, and provenance
