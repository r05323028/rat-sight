# Tasks

## Specification

- [x] 1. Inspect existing NetworkX engine, API/UI contracts, source manifests, and current synthetic graph.
- [x] 2. Record source, topology, surface/underground, scientific, and public-contract boundaries.
- [x] 3. Complete adversarial review and retain conditional NO-GO until source gates pass.

## Source gate

- [x] 4. Obtain human-approved source contract for a small Taipei street network: identity, URL/version, license, pinned hash, CRS/axis order, stable IDs, geometry and topology semantics, coverage/currentness.
- [x] 5. Independently validate source bytes, geometry, CRS, bends, identifiers, intersections, direction rules, and missingness; do not use stormwater geometry as a street substitute.

## Implementation

- [x] 6. Add the smallest surface-only geometry-to-graph adapter, preserving original LineStrings and source provenance; leave `create_synthetic_graph()` unchanged.
- [x] 7. Extend movement output only with an explicitly reviewed trajectory/edge-geometry contract, deterministic seed behavior, unitless parameters, and `SIMULATED` metadata.
- [x] 8. Render source geometries and aggregate visits/trajectories without arbitrary straight node-link lines; keep underground layers separate.
- [x] 9. Add focused graph, geometry-preservation, deterministic simulation, API, and browser tests.

## Verification

- [x] 10. Obtain Modeler and Public Health review of assumptions, labels, uncertainty, and no-inference boundaries. Modeler PASS after directed-edge/dead-end fixes; Public Health PASS with wording guidance applied.
- [x] 11. Obtain QA browser verification against source geometry and Municipal Analyst usability verification on an approved isolated runtime. API/source geometry and browser workflow passed; pixel-level basemap alignment remains unverified.
- [x] 12. Run OpenSpec gate and stop at Ready for Human Review; do not archive without human scope approval. Gate PASS with scientific partial-verification warning.
- [x] 13. Restore the legacy synthetic study-area default and retain pinned OSM as an explicit selectable mode; return `SOURCE_NETWORK_UNAVAILABLE` with provisioning guidance when OSM is explicitly selected but its artifact is missing/checksum-mismatched. (Owner decision: restore synthetic default.) API/UI regressions pass; full backend 162 and web 79 tests pass.
