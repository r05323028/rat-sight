# Official Municipal Complaint Activity

## ADDED Requirements

### Requirement: Feasibility gate precedes implementation
The change SHALL verify the official source, reuse terms, CSV schema, record grain, dates, category values, duplicate behavior, privacy fields, and historical coverage before any implementation. Rodent-related qualification SHALL use an exact documented official category mapping, not fuzzy text matching.

#### Scenario: Rodent category cannot be defensibly isolated
- **WHEN** official categories combine rodent and unrelated complaints or the category semantics are unknown
- **THEN** the change SHALL record NO-GO and SHALL NOT implement rodent complaint analytics

### Requirement: Complaint activity remains administrative data
The system SHALL label qualifying output as municipal rodent-related complaint activity and SHALL keep it distinct from observations, confirmation, prevalence, intervention, movement, and risk.

#### Scenario: Dashboard displays monthly activity
- **WHEN** aggregate complaint counts are available
- **THEN** the UI SHALL show the official category and limitations and SHALL NOT claim how many rodents were present

### Requirement: Privacy-minimal aggregate contract
The implementation SHALL persist and expose only approved monthly aggregate fields and provenance; it SHALL not persist or expose names, contacts, descriptions, attachments, complaint IDs, or individual complaint records.

#### Scenario: Sensitive fields exist in the CSV
- **WHEN** source files contain additional personal or free-text fields
- **THEN** the importer SHALL exclude them and fail closed if required privacy assumptions are not verified

### Requirement: Reproducible aggregate verification
Any GO implementation SHALL validate dates, categories, duplicate handling, missing values, deterministic monthly aggregation, provenance, and idempotent persistence, with an independently computed source-total comparison.

#### Scenario: Import validation fails
- **WHEN** required fields, dates, categories, source identity, or duplicate semantics are invalid
- **THEN** the importer SHALL make no partial writes and SHALL report exclusion/failure reasons
