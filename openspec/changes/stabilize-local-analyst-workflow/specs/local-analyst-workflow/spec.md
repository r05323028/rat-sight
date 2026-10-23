# Spec Delta

## ADDED Requirements

### Requirement: Reproducible local runtime

The repository MUST document one repeatable local launch path with configurable, non-conflicting API and web ports. The path MUST result in a browser-hydrated dashboard whose controls can reach the API. Runtime instructions MUST require ownership checks and MUST NOT terminate unrelated processes or use a shared database volume for disposable verification.

#### Scenario: Loopback browser

- **WHEN** the documented runtime is launched and opened using its documented host origin
- **THEN** React hydration succeeds in a fresh browser, API health is reachable, and a dashboard interaction produces its expected API request from the documented browser origin

### Requirement: Taipei-local report filtering

The dashboard MUST accept report date-times in `Asia/Taipei`, visibly identify that timezone, convert values to the existing UTC RFC3339 API parameters, and preserve inclusive start/end semantics and local range validation.

#### Scenario: Inclusive local range

- **WHEN** an analyst enters a valid Taipei-local range
- **THEN** requests use equivalent UTC bounds without machine-timezone dependence and the UI states that both selected boundaries are inclusive; for example `2026-10-01 08:30` Asia/Taipei becomes `2026-10-01T00:30:00Z`

#### Scenario: Filtered empty

- **WHEN** a valid local range matches no returned reports
- **THEN** the UI states that no records match the selected filters and does not imply zero incidents

### Requirement: Honest layer controls

The dashboard MUST make visible-layer counts precise, distinguish data availability from map visibility, and avoid disabled controls for unsupported interactions. Implemented synthetic and reference layers MUST retain classifications and provenance.

#### Scenario: Unsupported catalog entry

- **WHEN** a catalog entry has no supported map interaction
- **THEN** it is identified as unavailable/planned without a checkbox, while supported map layers have actionable visibility controls; displayed count equals visible rows and each row appears once

### Requirement: Honest truncated report results

The dashboard MUST distinguish returned feature count from total matching records and MUST clearly state when the bounded API response is truncated. It MUST preserve separate loading, storage-empty, filtered-empty, viewport-suppressed, service-error, and available states.

#### Scenario: Truncated response

- **WHEN** the API returns `truncated: true`
- **THEN** the UI labels the count as returned/shown and tells the analyst that additional matching records exist beyond the response, without claiming an exact total or adding a count endpoint
