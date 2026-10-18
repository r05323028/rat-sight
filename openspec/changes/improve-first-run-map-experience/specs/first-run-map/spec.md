# Spec Delta

## ADDED Requirements

### Requirement: First-run data status

The dashboard MUST distinguish loading, service error, storage-empty, filtered-empty, viewport-suppressed, and available states for each implemented layer. It MUST provide concise next-step guidance for unloaded official data and MUST NOT represent unavailable data as zero observations.

#### Scenario: Empty official layer

- **WHEN** an official layer has no imported records
- **THEN** the dashboard states that local data is not imported and gives the supported setup action without exposing developer internals as an analyst control

#### Scenario: Broad viewport

- **WHEN** the bounded query is suppressed because the viewport exceeds the API span limit
- **THEN** the dashboard explains that the user must zoom in and does not imply the dataset is absent

### Requirement: Layer catalog clarity

The dashboard MUST group or otherwise visibly distinguish implemented official reference layers, synthetic report/simulation layers, and planned unavailable capabilities. Counts and toggle enablement MUST reflect actual layer availability.

#### Scenario: Synthetic layer

- **WHEN** a synthetic report or simulation layer is shown
- **THEN** its `SIMULATED` classification and fixture status are visible adjacent to its control or result

### Requirement: Synthetic preview interpretation

Before and after a preview, the dashboard MUST state that output is a synthetic simulated fixture, not real observations or administrative findings. Result metrics MUST NOT be presented as animal counts, movement, hotspot, risk, prevalence, completeness, or intervention evidence; parameters and seed remain visible.

#### Scenario: Preview completed

- **WHEN** a preview returns successfully
- **THEN** the result panel shows synthetic-only wording, uncertainty-not-estimated wording, parameters/seed, and prohibited interpretation guidance

### Requirement: Understandable report filtering

Rodent report filtering MUST identify UTC semantics, inclusive start/end behavior, the filtered feature count, and explicit empty/error states. Existing UTC API contract and range validation MUST remain compatible.

#### Scenario: Filtered miss

- **WHEN** a valid range returns no matching reports
- **THEN** the dashboard says no records match the selected filters and does not imply no incidents occurred
