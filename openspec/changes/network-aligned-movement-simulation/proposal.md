# Proposal

## Feasibility decision

**Ready for Human Review.** A bounded OSM extract is now pinned and validated under ODbL 1.0 with explicit CRS, checksum, coverage, topology rules, and attribution. Surface graph construction, geometry-preserving trajectories, API provenance, UI controls, focused tests, QA, Modeler, Public Health, Reviewer, and browser workflow evidence are complete. Pixel-level basemap alignment remains unverified; the extract is not a Taipei-wide inventory. Do not archive until owner acceptance.

## Why

The current deterministic graph is a useful schematic demonstration but its straight node-to-node lines are not geographic streets. A future small vertical slice should allow a synthetic random walk over verified surface-network geometry while preserving the existing schematic graph for tests and demonstrations.

## What Changes

- Define a source-verification gate for one small Taipei street-network fixture.
- Separate source ingestion, graph construction, movement simulation, and visualization contracts.
- Preserve original bent LineStrings and traceable source IDs in graph edges and rendered GeoJSON.
- Reuse NetworkX weighted random-walk primitives where compatible.
- Add deterministic trajectory/aggregate-edge output only after the source gate and model/public-health approvals pass.
- Keep all outputs `SIMULATED`, explicitly hypothetical, uncalibrated, and non-decision evidence.
- Evaluate sewer/drainage geometry separately; never combine surface and underground networks from intersection/proximity alone.

## Integrity Boundary

A network-constrained synthetic path is a generated scenario, not an observed route or migration. Edge visitation is model output, not a report count, population estimate, hotspot, risk, prevalence, or intervention effect. Existing `create_synthetic_graph()` remains unchanged and available.
