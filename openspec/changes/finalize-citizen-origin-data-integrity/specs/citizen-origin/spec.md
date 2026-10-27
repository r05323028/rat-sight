# Citizen-report simulation origins

## ADDED Requirements

### Requirement: Snapshot-bound simulation origins
The system MUST bind every citizen-report simulation origin to the exact published snapshot the analyst reviewed. An OSM aggregate-cell request MUST carry `origin_cell_id` together with `origin_source` naming the dataset id, resource version, and content SHA-256 of the snapshot used for selection; the backend MUST resolve the cell only inside that snapshot and MUST NOT fall back to a newer version, a different digest, client-supplied geometry, or a nearest cell.

#### Scenario: matching snapshot resolves
- **WHEN** the request carries the currently published dataset id, resource version, and content digest for an eligible cell
- **THEN** the API resolves that cell inside the same snapshot and runs the preview

#### Scenario: stale resource version
- **WHEN** the request names a resource version that is no longer the published one
- **THEN** the API returns `409 ORIGIN_SOURCE_VERSION_CONFLICT` with the requested dataset id, version, and refresh action, and does not run a simulation against the newer import

#### Scenario: stale content digest
- **WHEN** the request names the published version but a different content SHA-256
- **THEN** the API returns the same `409 ORIGIN_SOURCE_VERSION_CONFLICT` rather than resolving a cell by identity alone

#### Scenario: unknown dataset
- **WHEN** the request names a dataset id with no published snapshot
- **THEN** the API returns `422 ORIGIN_SOURCE_UNKNOWN` and no cell geometry

### Requirement: Fail-closed snapshot resolution
Resolution MUST read the published version and content digest together and MUST return the cell geometry, provenance, classification, and count from one pinned row query. The system MUST apply published-cell existence, suppression, classification, and provenance-consistency checks to that row only, and MUST fail closed instead of substituting any other snapshot.

#### Scenario: removed cell
- **WHEN** the selected cell identity does not exist in the named snapshot
- **THEN** the API returns `422 ORIGIN_CELL_NOT_RESOLVABLE` and runs nothing

#### Scenario: suppressed cell
- **WHEN** a stored row for the selected cell does not meet the suppression minimum
- **THEN** the API returns the same `422 ORIGIN_CELL_NOT_RESOLVABLE` response as an absent cell, so the response cannot confirm that a suppressed cell exists

#### Scenario: stored provenance disagrees with the request
- **WHEN** the row's stored provenance names a different version or digest than the verified snapshot
- **THEN** the API fails closed with an unresolvable-origin error instead of using the row

#### Scenario: client geometry
- **WHEN** a request attempts to supply its own origin geometry or bypass published-cell identity
- **THEN** the request is rejected by the request schema

### Requirement: Report-category origin eligibility
The system MUST enforce one centralized origin-eligibility policy: `sighting` is an eligible candidate-origin category, while `bait_station`, `other`, and unknown categories are context-only and MUST NOT start a simulation. The policy MUST be applied by the backend, MUST expose its reason and policy version, and MUST NOT be overridable by the client.

#### Scenario: eligible sighting
- **WHEN** a published `sighting` cell is selected
- **THEN** the preview runs and the response records the category, eligibility, and policy version

#### Scenario: bait-station or other category
- **WHEN** a request selects a `bait_station` or `other` cell
- **THEN** the API returns `422 ORIGIN_REPORT_TYPE_INELIGIBLE` with the reason, category, policy version, and `UNVERIFIED` classification, and runs no simulation

#### Scenario: unknown category cannot bypass
- **WHEN** a category is not in the policy
- **THEN** the policy treats it as context-only and the API rejects it

#### Scenario: context-only markers stay inspectable
- **WHEN** the map lists a context-only report
- **THEN** its details remain available with an explanation that it cannot serve as a simulation origin

### Requirement: Snapshot provenance in simulation output
Every citizen-report preview MUST report the snapshot it actually used: dataset id, resource version, content SHA-256, report category, category eligibility, eligibility policy version, origin resolution method, resolver version, candidate count, selected cell identity, network source identity, model version, and random seed. Citizen-report provenance MUST stay distinct from OSM network provenance, and the response MUST NOT describe a report cell as a verified animal origin.

#### Scenario: provenance identifies the snapshot
- **WHEN** a preview succeeds
- **THEN** the response contains the dataset id, resource version, and content digest of the resolved snapshot, separate from the network source fields

#### Scenario: deterministic replay
- **WHEN** the same snapshot, cell, model, and seed are requested twice
- **THEN** both responses resolve the same candidate nodes and produce the same trajectories

### Requirement: Source-refresh selection integrity
The dashboard MUST keep a selected citizen-report origin bound to the snapshot it came from. A real change of dataset, resource version, or content digest MUST invalidate an incompatible selection and preview; a viewport-only refresh or refetch that returns the same source identity MUST NOT invalidate them. An in-flight preview MUST NOT overwrite the result of a newer selection or snapshot.

#### Scenario: source version changes
- **WHEN** refreshed aggregates publish a different resource version or digest than the selected origin
- **THEN** the dashboard clears the selection and preview and shows an actionable refresh notice

#### Scenario: viewport refresh
- **WHEN** the aggregate query refetches for a new map viewport and returns the same source identity
- **THEN** the selected marker, preview, and playback stay intact

#### Scenario: conflict response
- **WHEN** a preview returns `409 ORIGIN_SOURCE_VERSION_CONFLICT`
- **THEN** the dashboard shows the refresh instruction and does not present the previous preview as current

### Requirement: Published-cell coverage diagnostics
The repository MUST provide a repeatable diagnostic that evaluates the current published aggregate snapshot against a pinned network. It MUST report published, eligible, resolved, and zero-candidate counts, candidate distribution, provenance, and drift against a previous run. It MUST NOT hardcode an expected cell count, treat a missing cell as a zero report, or snap an unresolvable cell to a distant road.

#### Scenario: full resolution
- **WHEN** every eligible cell has at least one strictly in-cell candidate
- **THEN** the report shows resolved equal to eligible with zero zero-candidate cells, alongside the network snapshot identity

#### Scenario: coverage gap
- **WHEN** a cell has no in-cell candidate
- **THEN** the report lists it as unresolvable with a reason and does not fail the run or invent a candidate

#### Scenario: snapshot drift
- **WHEN** the diagnostic is compared with a previous report
- **THEN** it reports version, digest, cell, resolution, and network changes

### Requirement: Measured simulation performance
Performance claims MUST be supported by a repeatable benchmark that records the environment, network snapshot, snapshot identity, and seed, and measures cold and warm graph load, candidate resolution, walk execution, reachability, serialization, payload size, approximate memory, and end-to-end preview latency at documented walker/step configurations. Optimizations MUST follow measurement and MUST preserve outputs and provenance.

#### Scenario: recorded measurement
- **WHEN** the benchmark runs against a pinned snapshot and network
- **THEN** it writes a report containing the environment, provenance, and each measured stage

#### Scenario: optimization preserves results
- **WHEN** a traversal or caching change is made to reduce latency
- **THEN** regression tests show identical reachability, component, and preview results
