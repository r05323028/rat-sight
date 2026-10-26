# Full local data bootstrap specification

## ADDED Requirements

### Requirement: Persistent project-scoped profile
The repository SHALL provide a `full-local` bootstrap command that starts or reuses a dedicated PostGIS Compose project and named volume, preserves imported data across API/Web restarts, and does not mutate shared projects or volumes.

#### Scenario: clean bootstrap
- **WHEN** an operator runs `make data-bootstrap PROFILE=full-local` with verified raw sources available
- **THEN** migrations and supported imports run in the dedicated project and the command prints a data inventory

#### Scenario: repeat bootstrap
- **WHEN** the operator repeats the same command with unchanged pinned sources
- **THEN** importer idempotency is preserved and no duplicate records are created

#### Scenario: inspect-only
- **WHEN** the operator runs the profile in inspect-only mode
- **THEN** source hash/CRS/format/profile checks run without database writes or volume deletion

### Requirement: Pinned inventory
The full-local inventory SHALL report 12 administrative district records for dataset `121199@20220915` and 19,747 stormwater records for the pinned resource version, while stating that these are pinned source-record counts rather than completeness or currentness claims. Official layers SHALL remain separate from the optional synthetic fixture.

#### Scenario: complete pinned inventory
- **WHEN** bootstrap completes with the verified source files
- **THEN** inventory reports 12 districts, 19,747 stormwater records, and zero synthetic reports unless explicitly requested

### Requirement: Explicit lifecycle status and teardown
The bootstrap SHALL expose `up`, `status`, and `down` actions. `status` SHALL report the owned project inventory or an unmigrated/not-running state. `down` SHALL preserve the persistent volume by default and SHALL delete it only with an explicit purge action; purge SHALL be rejected for other actions.

#### Scenario: status before migration
- **WHEN** the owned database is running without application tables
- **THEN** status reports not migrated and does not claim an empty dataset

#### Scenario: safe down
- **WHEN** the operator runs `down` without purge
- **THEN** only the owned project is stopped and its persistent volume remains

#### Scenario: explicit purge
- **WHEN** the operator runs `down --purge`
- **THEN** only the owned project volume is deleted; `--purge` on `up` or `status` is rejected

### Requirement: Pinned verified sources
The bootstrap SHALL use only the documented administrative-boundary and stormwater source identities, hashes, licenses, CRS transformations, and provenance. Hash, CRS, geometry, identity, or source-version mismatch SHALL fail before import.

#### Scenario: source mismatch
- **WHEN** a supplied archive does not match its pinned hash or importer validation
- **THEN** bootstrap preflights both sources, stops with an actionable error before either importer writes, and leaves persisted data unchanged

#### Scenario: failure after preflight
- **WHEN** an unexpected importer/storage failure occurs after the first import begins
- **THEN** bootstrap reports failure, never reports a complete inventory, and the owned environment can be discarded and recreated without affecting shared resources

### Requirement: Optional synthetic demo
Synthetic rodent reports MAY be loaded only through an explicit profile option and SHALL remain classified and displayed as `SIMULATED`, separate from official reference layers.

#### Scenario: default official profile
- **WHEN** the operator runs `full-local` without the synthetic option
- **THEN** no rodent fixture is imported and the inventory identifies only official reference layers

### Requirement: Populated dashboard semantics
The existing API and Dashboard SHALL continue using bounded viewport queries and truncation semantics while exposing imported layer availability, provenance, CRS, source version, and reference-only limitations.

#### Scenario: bounded exploration
- **WHEN** a user pans or zooms the populated map
- **THEN** API requests remain viewport-bounded and the UI distinguishes empty viewport results from empty storage

### Requirement: Candidate assessment boundary
The change SHALL document assessments of sanitary sewer pipelines, sewer manholes, and public trash bins, but SHALL not ingest a candidate whose source identity, license, CRS/axis order, or scientific/privacy limitations are unresolved.

#### Scenario: unresolved candidate
- **WHEN** a candidate lacks verified CRS or permitted reuse
- **THEN** it remains an explicit no-go/assessment record and no importer or data is added
