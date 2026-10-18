# Real Rodent Data Source Feasibility

## ADDED Requirements

### Requirement: Metadata-only source investigation
The project SHALL investigate Rat Radar, Taipei open-data, Taipei 1999 complaints, and relevant official rodent-related sources using documentation and non-sensitive metadata only. It SHALL NOT download, scrape, store, or import raw citizen-report records.

#### Scenario: Candidate evidence is traceable
- **WHEN** a candidate fact is recorded
- **THEN** the artifact identifies the source URL, verification date, evidence status, and limitation

### Requirement: Source comparison preserves semantics
The comparison SHALL distinguish citizen reports, platform-moderated reports, service requests, municipal inspections, confirmed observations, treatment records, and aggregate statistics.

#### Scenario: Candidate is not a confirmed observation
- **WHEN** a source exposes a report or moderation status
- **THEN** the recommendation SHALL NOT relabel it as an observation, infestation, prevalence, or municipal confirmation

### Requirement: Authorization and privacy blockers
The evidence SHALL explicitly document licensing, automated retrieval, redistribution, privacy, spatial precision, retention, and data-owner authorization requirements. Unknown terms SHALL remain `UNVERIFIED` or `BLOCKED`.

#### Scenario: Public endpoint lacks reuse terms
- **WHEN** a source is publicly visible but reuse or privacy terms are not verified
- **THEN** raw ingestion SHALL be `NO-GO` pending written authorization and field-level review

### Requirement: Proposed next implementation boundary
The change SHALL provide a source recommendation or NO-GO decision and a concise proposed contract covering provenance, classification, minimum fields, CRS, temporal semantics, privacy restrictions, validation, update strategy, and API behavior.

#### Scenario: Human approval is still required
- **WHEN** authorization or source semantics remain unresolved
- **THEN** the artifact SHALL identify the exact human decision and SHALL NOT implement ingestion
