# Spec Delta

## ADDED Requirements

### Requirement: Immutable smoke reset

The fixture-only smoke harness MUST run populated and storage-empty scenarios with the production rodent-report immutability trigger enabled. Its reset MUST affect only the disposable smoke database through an explicit test-only reset path and MUST NOT weaken production immutability or touch shared developer resources.

#### Scenario: Populated to empty transition

- **WHEN** the smoke harness clears its populated fixture
- **THEN** the empty scenario completes successfully, the trigger remains installed, and isolated cleanup removes only the smoke project resources

### Requirement: Consistent simulated classification

Persisted fixture rodent reports MUST have `data_class=RODENT_REPORT` and `classification=SIMULATED`. The API MUST validate stored classification and fail explicitly on inconsistent rows; it MUST NOT silently relabel them.

#### Scenario: Inconsistent stored row

- **WHEN** a persisted rodent report has a classification other than `SIMULATED`
- **THEN** the API returns an explicit non-2xx data-contract error and does not present the row as simulated

### Requirement: Bounded report inspection

The dashboard MUST show no more than 100 auxiliary report inspection buttons while retaining every returned feature in the MapLibre source. A returned feature selected directly on the map, including one outside the first 100, MUST show its details.

#### Scenario: Large response and map selection

- **WHEN** the API returns more than 100 reports and the user selects a report point on the map
- **THEN** the list shows a clear cap notice and the selected report details are displayed

### Requirement: Temporal validation and map interaction

The dashboard MUST reject an invalid temporal range locally before issuing an API request, show a clear validation message, and the live browser smoke MUST verify point selection, layer disablement, and stale selection removal.

#### Scenario: Invalid range

- **WHEN** `reported_from` is later than `reported_to`
- **THEN** no request is issued and the UI identifies the invalid range rather than reporting service unavailability
