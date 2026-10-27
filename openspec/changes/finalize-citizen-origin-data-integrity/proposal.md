# Finalize citizen-origin data integrity

## Why

`citizen-report-driven-simulation-origins` made published citizen-report cells selectable simulation origins, but three integrity gaps remained in the delivered workflow:

1. A selected origin was identified as `cell_id:month:report_type` and resolved against whatever aggregate version happened to be current at request time. Between the map load and the simulation request a new import could replace the snapshot, so the run silently used geometry and provenance the analyst never reviewed.
2. Every published report category was treated as an equally valid animal-origin candidate, even though a poison-bait-station report is not evidence of a rodent sighting.
3. Coverage and performance claims rested on one-off probes: no repeatable diagnostic for published-cell resolvability, and a ~4 s preview whose cost was assumed rather than measured.

This change closes those engineering gaps. It does not resolve the source-authorization or scientific-approval findings (CR-ORIGIN-001..004) that the originating change still carries.

## What Changes

- **Snapshot-bound origins**: OSM aggregate-cell preview requests must carry `origin_source` (dataset id, resource version, content SHA-256). The backend resolves the cell only inside that snapshot; a stale version or digest is a `409 ORIGIN_SOURCE_VERSION_CONFLICT` and is never retried against a newer import.
- **Fail-closed resolution**: version and digest are read together, then one pinned row query returns geometry, provenance, classification, and count from the same snapshot. Absent and suppressed cells are indistinguishable in error responses.
- **Category eligibility**: a single centralized policy marks `sighting` as the only eligible candidate-origin category; `bait_station` and `other` stay visible as context-only reports with a disabled simulation action and an explanatory message.
- **Provenance**: preview responses record the snapshot actually used (dataset, version, digest, category, policy version, resolution method, resolver version, candidate count) separately from OSM network provenance.
- **Refresh integrity**: the dashboard binds a selection to the snapshot it came from, invalidates only on a real source change, and never renders an older preview as if it belonged to refreshed data.
- **Coverage diagnostics**: a repeatable tool reports published cells, eligible origins, resolved/zero-candidate counts, candidate distribution, and drift against a previous snapshot.
- **Measured performance**: a benchmark tool records cold/warm load, candidate resolution, walk, reachability, serialization, payload size, memory, and end-to-end latency, plus the optimization it justified.

## Impact

- Affected spec: `citizen-origin` (delta). This capability currently exists only as a pending delta in `citizen-report-driven-simulation-origins`, so this change adds requirements without modifying shipped main specs.
- Affected code: `services/api/src/ratsight_api/{api/schemas.py,api/routes/simulations.py,application/citizen_report_aggregates.py,application/simulation_preview.py,domain/citizen_report_aggregates.py}`, `packages/simulation/src/ratsight_simulation/graph/network.py`, `apps/web/src/{lib/api.ts,components/dashboard.tsx,app/globals.css}`, `scripts/citizen_origin_coverage.py`, `scripts/benchmark_simulation.py`.
- Compatibility: `origin_source` becomes required for `taipei_osm_songshan` cell origins and is rejected for `taipei_synthetic_demo`; response provenance fields are additive; no schema migration, no new service, database, cache, or queue.
- Data classification: citizen-report inputs stay `UNVERIFIED`; simulation output stays `SIMULATED`; no counts become animal counts, walkers, or weights.
