# Geospatial movement simulation

## ADDED Requirements

### Requirement: Explicit synthetic origin
The simulation SHALL accept an optional eligible graph-node origin, validate it against the selected network, echo its node ID and coordinates, and label it as a synthetic model input rather than an observed animal origin.

#### Scenario: selected origin
- **WHEN** a user selects a returned eligible network node and runs a simulation
- **THEN** all trajectories use that node, the response records it, and the UI shows its synthetic/non-observational meaning

#### Scenario: invalid origin
- **WHEN** a request names a node absent from the selected graph
- **THEN** the API returns a validation error and does not silently snap or substitute another origin

### Requirement: Deterministic step identity
Each returned trajectory edge SHALL include an explicit zero-based step index, preserving order and seed reproducibility.

#### Scenario: repeated run
- **WHEN** identical study area, origin, parameters, and seed are submitted twice
- **THEN** trajectory step indexes, edge IDs, geometry, and aggregate results match

### Requirement: Stepwise synthetic playback
The frontend SHALL provide step-indexed playback derived from a completed response, with play/pause, previous/next, reset, current-step display, and trajectory selection where trajectories exist.

#### Scenario: explore trajectory
- **WHEN** a user switches to trajectory mode and advances playback
- **THEN** only returned synthetic edge geometry through the selected step is shown, with `SIMULATED` and step semantics visible

#### Scenario: reduced motion or unavailable trajectory
- **WHEN** reduced motion is requested or trajectories are absent/truncated
- **THEN** playback avoids camera/animal animation and states the available bounded output and limitation

### Requirement: Honest reachability and termination
The UI and API SHALL distinguish graph dead-end termination, disconnected/unvisited network areas, and absence of trajectories without treating zero visits as zero rodents or observed absence.

#### Scenario: dead end
- **WHEN** a synthetic walker reaches a graph dead end
- **THEN** the result reports graph termination and does not render a biological arrival or movement finding

### Requirement: Preserve evidence boundaries
The simulation SHALL retain source/license/CRS/provenance, bounded surface-network scope, `SIMULATED` output classification, independent report fixtures, and no stormwater traversability inference.

#### Scenario: inspect result provenance
- **WHEN** a user opens simulation results
- **THEN** origin, seed, model/version, source identity, geometry scope, uncertainty, and non-inference warning remain available beside output
