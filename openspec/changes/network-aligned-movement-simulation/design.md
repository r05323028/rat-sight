# Design

## Current gate

No implementation starts until a street source contract is approved: publisher/resource identity, retrieval date, license, pinned hash, explicit CRS/axis order, stable source IDs, geometry validity, coverage, topology semantics, and currentness/limitations. Geofabrik Taiwan OSM is the candidate source: ODbL 1.0, OSM node/way IDs, WGS84 coordinates, and shared-node topology. Its mutable snapshot, exact bytes/hash, extract boundary, attribution/Produced Work obligations, and routing-tag semantics still require retrieval and review. The current verified stormwater source is not a street topology source and cannot be converted into one by intersection/proximity.

## Four independent layers

1. **Persistent GIS ingestion:** acquire and validate a source-verified surface street fixture, preserving original LineStrings and provenance. This is separate from PostGIS administrative/stormwater reference ingestion.
2. **Graph construction:** derive a NetworkX graph from source geometry only after an explicit topology contract. Nodes represent source-confirmed intersections/endpoints; edges retain source ID, full bent geometry, CRS, and classification. Geometry crossing alone does not create underground connectivity.
3. **Movement simulation:** reuse weighted random-walk primitives. Parameters remain hypothetical, unitless, deterministic by seed, and explicitly uncalibrated. Existing schematic `create_synthetic_graph()` remains unchanged.
4. **Visualization:** render edge visitation and trajectories from stored LineString geometry, never `[start_node, end_node]` straight segments. API output must carry source IDs, graph provenance, model/version, seed, parameters, and `SIMULATED` classification.

## Surface/underground boundary

The first slice is surface-only. Underground stormwater/sewer geometry remains a separate reference layer. No combined graph or transition edge is allowed without source-confirmed connectivity and an approved transition assumption.

## Acceptance shape

A small fixture with at least one bend and one intersection proves geometry preservation. Browser QA compares rendered GeoJSON coordinates to source geometry and verifies no arbitrary straight-line replacement. QA and Municipal Analyst inspect labels, provenance, reproducibility, and non-inference wording; Modeler and Public Health review assumptions and limits.
