# Citizen-report-driven simulation origins

## ADDED Requirements

### Requirement: Approved aggregate origin use
The system MUST keep citizen aggregates independent from simulation unless a recorded human decision explicitly authorizes derived-origin use. Source reuse, privacy, and scientific approvals remain required before claiming approved use; an explicit project-owner override MAY authorize bounded engineering execution while those approvals are open, provided the override and residual risk are recorded and all outputs remain `UNVERIFIED` and `SIMULATED` as appropriate.

#### Scenario: no recorded decision
- **WHEN** neither approvals nor a recorded project-owner override authorizes derived-origin use
- **THEN** aggregate cells remain display-only and simulation cannot use them as origins

#### Scenario: owner-directed bounded activation
- **WHEN** the project owner records an override permitting one explicitly selected published aggregate cell as a simulation origin while source and scientific approvals remain open
- **THEN** the API MAY resolve that cell to eligible strictly in-cell network nodes and run a simulation
- **AND** a single candidate uses `strict-in-cell-v1`; multiple candidates seed walkers uniformly with the seeded RNG under `uniform-in-cell-v1`
- **AND** provenance records the override, `UNVERIFIED` source status, resolver version, candidate count, representative node, full candidate list, and explicit cell identity
- **AND** report count, category, and month do not become animal count, origin certainty, or movement weight
- **AND** UI copy does not claim legal reuse, approved source terms, or approved biological semantics

### Requirement: Privacy-preserving cell identity
An origin request MUST use stable dataset/version/cell/month/type identity, preserve suppression, and expose no exact source coordinates, free text, photos, or unsuppressed groups.

#### Scenario: eligible cell
- **WHEN** an eligible aggregate cell is selected
- **THEN** the API validates its identity and returns the cell's coarse geometry and provenance without reconstructing source reports

### Requirement: Deterministic candidate resolution
The backend MUST resolve eligible cells to in-cell network candidates using a documented deterministic rule, report CRS/coverage/uncertainty, and reject no-candidate cases without distant snapping. Under the current owner-directed bounded mode, one candidate is a strict origin and multiple candidates seed walkers uniformly with the seeded RNG; approval of that candidate/ambiguity rule remains open.

#### Scenario: no candidate
- **WHEN** a selected cell has no eligible network candidate within supported coverage
- **THEN** the API returns an actionable no-candidate error and does not substitute a default origin

#### Scenario: multiple in-cell candidates
- **WHEN** a selected cell has more than one eligible in-cell network node
- **THEN** the API seeds walkers uniformly across all eligible nodes using the recorded random seed and records the full node list
- **AND** the representative node is the first sorted node, not a claim that one node is the observed origin

### Requirement: Separate cell and simulation origin
The response MUST distinguish the selected report cell (`UNVERIFIED`) from the resolved internal graph node(s) and simulation output (`SIMULATED`); report count/category/month MUST NOT silently become animal count, origin certainty, or movement weight.

#### Scenario: run from cell
- **WHEN** an eligible cell is resolved and simulated
- **THEN** provenance shows cell identity, resolution method, resolved node(s), seed, and synthetic limitations

### Requirement: Analyst workflow hides technical graph nodes
After bounded activation, the primary workflow MUST select eligible aggregate cells, not graph nodes; focusing or selecting a cell MUST NOT execute a run, and failed runs MUST not retain stale results.

#### Scenario: select cell
- **WHEN** an analyst selects an eligible aggregate cell
- **THEN** the UI shows coarse report-region semantics and enables simulation only after backend eligibility confirmation

### Requirement: Explicit analyst origin contract
Public OSM previews MUST require an explicit eligible `origin_cell_id` and reject missing, node-based, mixed, or ineligible origins. The API MUST NOT substitute a default graph origin or synthetic fallback. The isolated `taipei_synthetic_demo` MAY use explicit fixture origins only when separately selected.

#### Scenario: missing or graph-node origin
- **WHEN** a public OSM preview request omits `origin_cell_id` or supplies `origin_node_id`
- **THEN** the API returns an actionable validation error and runs no simulation

#### Scenario: ineligible cell
- **WHEN** the supplied aggregate cell is unknown, suppressed, unavailable, stale, or has no eligible in-cell node
- **THEN** the API fails closed with a specific error and does not choose another cell or default node

### Requirement: Playback and stale-result isolation
The dashboard MUST offer aggregate and individual views, walker selection, play/pause, previous/next, and reset over returned simulated steps. Steps MUST be labeled as sequence steps, playback MUST stop at the final step and clean up timers. Changing the focused cell, study area, or run MUST clear or identify prior output, disable or reset incompatible playback, and allow only the latest request to update results.

#### Scenario: focused cell changes
- **WHEN** a user selects a different citizen-report cell after a simulation completed
- **THEN** the prior trajectories are not silently relabeled as that new cell's result and the next action is clear

#### Scenario: out-of-order responses
- **WHEN** an older preview response arrives after a newer request
- **THEN** it cannot replace the newer result or its playback state

### Requirement: Focused aggregate-cell detail card
The analyst UI MUST let an aggregate marker be focused to inspect aggregate-only details without treating focus as an origin selection or starting a run. The card MUST show cell identity, month, report type, published count, the 250 m centroid caveat, `UNVERIFIED` classification, and attribution.

#### Scenario: focus a marker
- **WHEN** an analyst clicks or activates a published aggregate cell marker
- **THEN** the marker is highlighted and a detail card shows the aggregate details and provenance
- **AND** no preview request is sent and the simulation origin is unchanged

#### Scenario: run from the focused cell
- **WHEN** an analyst activates the explicit run action for the focused cell
- **THEN** the preview request sends that cell's stable `cell_id`/month/report-type identity as `origin_cell_id` without `origin_node_id`
- **AND** the output remains `SIMULATED` and the report count is never a walker count or movement weight

### Requirement: Published-cell coverage and map subset disclosure
The pinned network MUST cover every aggregate cell currently offered as a simulation origin. The preview API MAY return a smaller local reference subset for map rendering, but MUST disclose that subset and keep simulation and reachability on the full model graph.

#### Scenario: every published cell has coverage
- **WHEN** the dashboard lists currently published aggregate cells as possible origins
- **THEN** the pinned network contains at least one strictly in-cell graph node for every listed cell
- **AND** a cell with zero candidates fails closed and is not silently replaced by another origin

#### Scenario: local visualization subset
- **WHEN** the API returns fewer graph nodes or edges than the full model graph for map rendering
- **THEN** the response reports `local_reference` mode, the subset radius, and returned versus full node and edge counts
- **AND** reachability totals are computed on the full graph
- **AND** the UI labels the subset and does not present it as full network coverage

### Requirement: Synthetic fixture origin isolation
The analyst UI MUST keep optional synthetic fixture-origin selection separate from citizen-report aggregate selection.

#### Scenario: Explicit synthetic fixture request
- **WHEN** an operator selects bounded fixture `synthetic-cell-n0` on `taipei_synthetic_demo`
- **THEN** the preview request sends `origin_cell_id` without `origin_node_id`, and UI identifies fixture as synthetic with no correspondence to Rat Radar or any citizen-report cell
- **AND** selecting an aggregate cell alone does not populate `origin_cell_id`
- **AND** this control is unavailable outside the synthetic demo study area
