# Network-aligned movement specification

## ADDED Requirements

### Requirement: Verified surface network source
The change SHALL require an approved, pinned surface street-network source before ingestion or graph construction. The source contract SHALL include publisher/resource identity, license, hash, CRS/axis order, stable IDs, geometry validity, coverage, topology semantics, and limitations.

#### Scenario: no verified source
- **WHEN** no source contract with inspected bytes and explicit CRS/topology semantics exists
- **THEN** implementation stops at conditional NO-GO and does not download, ingest, graph, or simulate from a street source

### Requirement: Geometry-preserving graph
A constructed surface graph SHALL retain each source LineString's bends, source ID, CRS, and provenance on its edges. Intersections SHALL create graph connectivity only when supported by the source topology contract; geometric proximity or underground intersection alone SHALL not create transitions.

#### Scenario: bent source edge
- **WHEN** a source edge contains intermediate coordinates
- **THEN** graph and rendered GeoJSON retain those coordinates and do not replace the edge with a two-point straight segment

### Requirement: Deterministic network-constrained simulation
The movement slice SHALL reuse the existing NetworkX engine where appropriate, accept explicit seed/walkers/steps/parameters, remain deterministic for a fixed seed, and classify every result `SIMULATED`. Parameters SHALL be hypothetical, unitless, uncalibrated, and visibly disclosed.

#### Scenario: reproducible run
- **WHEN** the same verified graph and simulation parameters are run with the same seed
- **THEN** aggregate edge visits and any trajectory output are identical; changing the seed may change output without implying validation

### Requirement: Honest visualization and provenance
The Dashboard/API SHALL distinguish network-constrained synthetic paths from observations and reference geometry, show model/version/seed/parameters/source graph/CRS/processing provenance, and state that uncertainty is not estimated and outputs cannot support hotspot, risk, prevalence, movement, or intervention claims.

#### Scenario: browser inspection
- **WHEN** a user enables the network-aligned synthetic layer
- **THEN** the map renders original source geometries, labels output `SIMULATED`, and inspection exposes source IDs and limitations without claiming observed movement

### Requirement: Separate surface and underground networks
The first slice SHALL be surface-only. Stormwater/sewer geometry SHALL remain a separate reference layer unless source-confirmed connectivity, transition assumptions, and scientific review authorize a later combined model.

#### Scenario: underground geometry present
- **WHEN** a stormwater or sewer feature intersects a surface edge geometrically
- **THEN** no movement transition or combined graph edge is inferred from that intersection

### Requirement: Pinned OSM network is the default study area
The Dashboard and API SHALL default to `taipei_osm_songshan`, so a preview that omits `study_area` follows the pinned surveyed network. The schematic `taipei_synthetic_demo` graph SHALL remain explicitly selectable, SHALL be drawn as straight node-to-node links (dashed in the UI) with its topology disclosed, and SHALL never be presented as road geometry.

#### Scenario: default preview
- **WHEN** a user opens the dashboard and runs the default preview while the pinned artifact is provisioned
- **THEN** the `taipei_osm_songshan` graph is used and output remains labeled `SIMULATED`

#### Scenario: schematic study area selected
- **WHEN** a user explicitly selects `taipei_synthetic_demo`
- **THEN** the schematic graph is used, its straight-line topology is disclosed as non-road geometry, and output remains labeled `SIMULATED`

### Requirement: Source unavailability is explicit
When the pinned OSM source network is requested — by default or explicitly — and its artifact is missing or its checksum differs, the API SHALL return a typed source-unavailable error and the UI SHALL show provisioning guidance. The UI SHALL NOT render schematic endpoint lines as a substitute for a requested source network.

#### Scenario: missing source
- **WHEN** the pinned `taipei_osm_songshan` source artifact is absent or mismatched for a requested preview
- **THEN** preview returns `SOURCE_NETWORK_UNAVAILABLE` with expected path/provisioning guidance and no simulation geometry is rendered

### Requirement: Synthetic reports remain independent display-only data
The synthetic `RODENT_REPORT` fixture MAY contain points inside the bounded study area, but reports and simulated paths SHALL remain independent. No report identifier, trajectory identifier, report-seeded start, or report-derived movement weight SHALL be introduced.

#### Scenario: co-located fixture report and simulation
- **WHEN** a user enables both report and simulated network layers
- **THEN** both render independently with `RODENT_REPORT · SIMULATED` and `SIMULATED` classifications, and the UI states that co-location is not validation or evidence that either establishes the other
