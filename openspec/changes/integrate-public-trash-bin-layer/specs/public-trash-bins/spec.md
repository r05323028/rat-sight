# Public Trash Bin Reference Layer

## ADDED Requirements

### Requirement: Verified official source and geometry
The layer SHALL use a verified official resource, license, CRS, schema, source hash, and deterministic identity/duplicate policy before import.

#### Scenario: Essential source property is unknown
- **WHEN** CRS, source relationship, identity, or reuse terms cannot be verified
- **THEN** implementation SHALL stop with a documented NO-GO and shall not fabricate geometry or facility identity

### Requirement: Environmental reference semantics
The layer SHALL be labeled public-cleanliness facility reference data and SHALL remain distinct from rodent observations, food availability, infestation, risk, movement, and simulation.

#### Scenario: User inspects a bin
- **WHEN** a facility point is selected
- **THEN** the UI SHALL show source attributes and limitations without implying rodent activity or causal risk

### Requirement: Validated immutable point import
The importer SHALL validate source identity/hash, encoding, required fields, CRS, coordinates, duplicates, and transactional idempotency; it SHALL report imported, rejected, and duplicate counts and fail without partial writes.

#### Scenario: Invalid or duplicate source rows occur
- **WHEN** a row has malformed coordinates or violates the verified duplicate policy
- **THEN** the importer SHALL reject or deterministically deduplicate it with an explicit reason

### Requirement: Bounded selectable API and map layer
The API SHALL return bounded EPSG:4326 Point GeoJSON with bbox filtering, provenance, classification, and explicit empty/error states; the dashboard SHALL support toggling and selecting returned points.

#### Scenario: No facilities are imported
- **WHEN** the endpoint is queried before import
- **THEN** it SHALL return an explicit empty state and the UI SHALL not fabricate points
