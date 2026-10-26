# Map exploration experience

## ADDED Requirements

### Requirement: First-run orientation
The dashboard SHALL explain its purpose, available evidence classes, current unavailable/verified state, and prohibited conclusions before the primary simulation action.

#### Scenario: first visit
- **WHEN** a first-time user opens the dashboard
- **THEN** they can identify what is available, what is synthetic/unverified, and what cannot be concluded without opening technical details

### Requirement: Map-first task flow
The map SHALL remain the primary workspace while controls are grouped by orientation, map context, synthetic demonstration, records, and provenance. Secondary details SHALL use progressive disclosure.

#### Scenario: inspect geography
- **WHEN** a user selects an available geographic feature
- **THEN** a concise contextual summary appears near the map and detailed attributes remain optional

### Requirement: Honest synthetic demonstration
The default simulation action SHALL use sensible bounded parameters and clearly state `SIMULATED`, synthetic inputs/outputs, unitless weights, uncertainty not estimated, and no observed movement/risk/prevalence/hotspot/intervention claim.

#### Scenario: run simulation
- **WHEN** a user starts the demonstration
- **THEN** loading, completion, failure, output mode, provenance, and limitations are visible without interpreting output as observation

### Requirement: Actionable data states
Unavailable, loading, empty, filtered-empty, viewport-suppressed, service-error, and available states SHALL be distinguishable and provide next action where possible. Absence SHALL never imply zero incidents.

#### Scenario: unavailable source
- **WHEN** a layer source is unavailable or a viewport is too broad
- **THEN** the UI identifies the state, explains the bounded-data reason, offers the documented next step, and does not display zero as an observation count

### Requirement: Accessible responsive workflows
Primary controls, layer toggles, date filters, errors, and simulation results SHALL have accessible names, keyboard-visible focus, readable text, and usable desktop/mobile layouts.

#### Scenario: keyboard and narrow viewport
- **WHEN** a user navigates with keyboard at desktop or 390px viewport
- **THEN** focus order, names, status/error announcements, disclosures, and evidence classifications remain usable without horizontal overflow

### Requirement: Independent synthetic reports
Synthetic report-shaped fixtures SHALL remain `RODENT_REPORT · SIMULATED`, separate from simulation outputs, with no join or validation implication. Date controls SHALL state Asia/Taipei boundaries and UTC conversion clearly.

#### Scenario: inspect synthetic report-shaped records
- **WHEN** a user enables the report-shaped fixture layer and applies a date preset
- **THEN** the UI keeps `RODENT_REPORT · SIMULATED` beside the records and filter result, states Asia/Taipei inclusive boundaries, and does not merge or use records to validate simulation output
