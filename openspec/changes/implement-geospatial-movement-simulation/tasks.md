# Tasks

## Evidence and design

- [x] 1. Inspect existing network MVP, identify fixed origin, static trajectories, missing step identity, and provenance limits.
- [x] 2. Obtain Backend, Frontend, Modeler, Public Health, QA, Reviewer, and Municipal Analyst feedback.
- [x] 3. Record bounded API/frontend design and scientific interpretation boundaries.

## Implementation

- [x] 4. Add optional validated `origin_node_id`, echo origin metadata, and explicit trajectory `step_index`. (API shipped: request field + top-level `origin` object {node_id, coordinates, selection, classification, note} + `parameters.origin_node_id` echo + zero-based `step_index`; unknown node returns 422 `ORIGIN_NODE_NOT_IN_GRAPH` with no snapping — services/api/src/ratsight_api/api/schemas.py, application/simulation_preview.py, api/routes/simulations.py. Diagnostics added additively: top-level `reachability` {origin_node_id, reachable_nodes, total_nodes, reachable_edges, total_edges, component_count, classification, note} from `reachability_summary` in packages/simulation/src/ratsight_simulation/graph/network.py, and per-trajectory `termination_reason` (`completed` | `dead_end` | `no_eligible_transition`) from the walk statistics)
- [x] 5. Add map node selection for returned eligible network nodes; reject invalid/outside selections without silent snapping.
- [x] 6. Add client-side step playback: current step, previous/next, play/pause, reset, trajectory selection, and accessible status.
- [x] 7. Render only returned network geometry through selected step; highlight current step without interpolation or time claims.
- [x] 8. Reconcile termination copy and disclose fixed/user-selected origin, disconnected/unvisited areas, truncation, unitless weights, and synthetic-only meaning. (`reachability` provides the disconnected-node counts and `termination_reason` the termination copy input; both are topology only.)

## Verification

- [x] 9. Backend/geo/simulation tests for origin validation, deterministic origin differences, step indexes, dead ends, and empty trajectories. (Backend/geo/simulation suite: 171 passed; added reachability, sink termination, and isolated-origin empty-trajectory coverage; API origin validation, deterministic differences, step indexes, and omitted-field synthetic-default route regression pass.)
- [x] 10. Frontend tests for playback state, reduced-motion behavior, step list, origin semantics, geometry slicing, and clearing stale output after failed runs. (87 frontend tests pass.)
- [x] 11. Real API browser verification at desktop/mobile with pointer origin selection and playback. (QA isolated populated/empty runtimes: API origin/422/step indexes, 1440×900 pointer flow, 390×844 touch flow, playback, truncation, termination copy, teardown; PASS with findings.)
- [ ] 12. Municipal Analyst black-box re-evaluation and Public Health/Modeler/Reviewer sign-off. (CR-008 compatibility concern resolved by owner-selected synthetic default and regression coverage; pre-existing F1 stormwater label mismatch remains. Required role sign-off and Municipal Analyst re-evaluation still pending.)
- [x] 13. Reconcile OSM source hash evidence before claiming source acceptance. (Current local bytes, loader expectation, and source records agree on SHA-256 `faae4ffd1bd42e57871bdedbfdcc6e82b3324a458db95034d4ec40f0a019e67e`; historical QA prefix `5831ea28d78c…` lacks exact prior snapshot bytes and remains UNVERIFIED, so it is not current-source evidence.)
- [x] 14. Run OpenSpec strict validation and quality gate; stop Ready for Human Review, no archive/commit/push. (Strict validation valid; `make openspec-gate CHANGE=implement-geospatial-movement-simulation` PASS with scientific partial-verification warning.)
