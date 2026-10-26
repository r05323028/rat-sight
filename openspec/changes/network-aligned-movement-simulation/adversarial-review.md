# Adversarial review

**Decision: PASS WITH LIMITATIONS for bounded MVP; Ready for Human Review pending final owner acceptance.** Source, model, and public-health gates were exercised for the pinned bounded extract. Rat Radar remains NO-GO and underground traversal remains out of scope.

### AR-NAMS-001 — BLOCKING — no verified street source

Resolved for this bounded slice: a pinned OSM XML extract is documented in `docs/infrastructure/taipei-osm-network-source.md`, with SHA-256, ODbL attribution, EPSG:4326 axis order, coverage, and shared-node topology rules. NLSC and city open-data references remain discovery-only. Existing stormwater geometry remains reference-only.

### AR-NAMS-002 — MAJOR — straight-line visualization and geometry loss

Resolved: API edges and trajectory steps carry source LineString geometry; the UI renders it directly. Endpoint fallback remains only for the legacy synthetic fixture. QA verified 73 bent edges and zero geometry mismatches.

### AR-NAMS-003 — MAJOR — scientific over-interpretation

Network paths, edge visits, and node visits can be misread as observed movement, counts, risk, or traversability. Required labels include `SIMULATED`, `SCHEMATIC NETWORK`, unitless weights, not observed movement, uncertainty not estimated, smallest slice/not representative, and explicit no-risk/no-prevalence/no-intervention limits.

### AR-NAMS-004 — MAJOR — surface/underground conflation

Geometric intersections or proximity do not establish sewer/stormwater connectivity or animal transitions. The first slice must be surface-only; any combined model requires a separate source, transition contract, scientific/public-health review, and human acceptance.

### AR-NAMS-005 — MEDIUM — public contract expansion

Resolved with reviewed contract: API now exposes bounded individual trajectories, edge geometry, truncation metadata, provenance, and deterministic parameters. Focused API tests pass; `create_synthetic_graph()` remains unchanged. Human owner acceptance is still required before archive.
