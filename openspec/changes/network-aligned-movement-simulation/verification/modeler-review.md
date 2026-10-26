# Modeler review

Status: CONDITIONAL NO-GO pending fixes; review identified and fixes were applied before final verification.

Findings addressed:

- Directed edge IDs were ambiguous for reverse edges. Reverse edges now carry a `:reverse` edge ID and unique graph key.
- Dead-end and constraint-exhaustion walks now terminate early with an explicit trajectory flag instead of failing the API request; zero-edge probability output is safe.
- Early-terminated empty trajectories are omitted from MapLibre LineString output.
- OSM provenance now carries source URL, resource version, license, attribution, coverage, and checksum.

Positive review: shared-node topology, preserved bends, one-way handling, deterministic RNG, unitless weights, synthetic graph preservation, and SIMULATED labels are correct. OSM geometry remains a spatial assumption, not biological evidence.
