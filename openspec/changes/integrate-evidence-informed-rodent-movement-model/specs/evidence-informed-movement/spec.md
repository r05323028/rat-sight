# Evidence-informed movement integration

## ADDED Requirements

### Requirement: Verified source contracts precede real ingestion
The system SHALL not ingest or redistribute real rodent, food-business, market, or sanitary-sewer records until source ownership, reuse terms, schema, CRS, stable identity, version/hash, coverage, privacy, and scientific semantics are verified and approved.

#### Scenario: unverified source
- **WHEN** a candidate source lacks an approved contract
- **THEN** it remains a documented candidate and no records are fetched or persisted

### Requirement: Report semantics remain separate from origins
The system SHALL distinguish report records from animal presence, species, abundance, origin, trajectory, and validation. Any future report-informed origin distribution SHALL retain source linkage, uncertainty, exclusions, precision, bias limitations, and explicit non-biological interpretation.

#### Scenario: report-shaped input
- **WHEN** a report is considered for a simulation origin
- **THEN** the result identifies it as report evidence with uncertainty and does not call it an animal origin or trajectory

### Requirement: Environment-aware transitions use inspectable evidence
The system SHALL only modify transition weights using versioned geographic features and explicitly documented assumptions. A proxy SHALL not be represented as food access, shelter, infestation, risk, or causal evidence. Unknown coefficients SHALL remain hypothetical and dimensionless.

#### Scenario: environment-aware run
- **WHEN** an approved scenario changes transition weights
- **THEN** the response exposes feature versions, assumptions, coefficients, and synthetic limitations

### Requirement: Surface and underground networks remain separate
The system SHALL not infer sewer/stormwater traversability or surface-to-underground transfers from intersections, proximity, or shared coordinates. Any future transfer requires source-confirmed connectivity and approved scientific semantics.

#### Scenario: crossing geometries
- **WHEN** an underground line intersects a surface line geometrically
- **THEN** no movement transfer is created without source-confirmed access and approval

### Requirement: Comparable scenarios expose differences
Baseline, report-origin, and environment-aware scenarios SHALL preserve seed, network, source versions, model version, parameters, provenance, diagnostics, and limitations so simulated differences are reproducible and inspectable.

#### Scenario: compare scenarios
- **WHEN** baseline and environment-aware runs are compared
- **THEN** their changed inputs and simulated output differences are shown without claiming accuracy improvement
