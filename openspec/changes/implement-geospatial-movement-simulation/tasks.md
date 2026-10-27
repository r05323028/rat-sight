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
- [x] 10. Frontend tests for playback state, reduced-motion behavior, step list, origin semantics, geometry slicing, and clearing stale output after failed runs. (91 frontend tests pass.)
- [x] 11. Real API browser verification at desktop/mobile with pointer origin selection and playback. (QA isolated populated/empty runtimes: API origin/422/step indexes, 1440×900 pointer flow, 390×844 touch flow, playback, truncation, termination copy, teardown; PASS with findings.)
- [ ] 12. Municipal Analyst black-box re-evaluation and Public Health/Modeler/Reviewer sign-off. (CR-008 behavior is implemented per user message m00160: omitted requests now return 422; authenticated project provenance for closure remains pending. F1 stormwater accessible-name mismatch is fixed and covered by focused dashboard plus real-browser desktop/mobile checks. Municipal Analyst re-evaluation now PASS on QA-owned `127.0.0.1:3086` → API `8005`; Public Health, Modeler, and Reviewer remain CONDITIONAL. Formal CR-008 provenance authentication remains pending.)
- [x] 13. Reconcile OSM source hash evidence before claiming source acceptance. (Current pinned expanded snapshot is 26,485,976 bytes, SHA-256 `9db94dd723445fb45e73a77dca4ee4a74783af26e04794fc3fc9d5f63aa0f868`, matching loader expectation and source records; old songshan `faae4ffd...` and QA prefix `5831ea28...` are historical/unverified, not current-source evidence.)
- [x] 14. Run OpenSpec strict validation and quality gate; stop Ready for Human Review, no archive/commit/push. (Strict validation valid; earlier gate run PASS with scientific partial-verification warning. The gate now also blocks on incomplete required tasks, so task 12 keeps this change below Ready.)
- [x] 15. Correct OSM direction semantics: retain `oneway` only as metadata, add bidirectional movement edges with reversed source geometry, preserve shared-node topology, and keep visual crossings disconnected. (Added `test_vehicle_oneway_metadata_does_not_remove_reverse_movement` and `test_visual_crossings_without_shared_osm_nodes_remain_disconnected`; pinned source checksum unchanged.)
- [x] 16. Reconcile the corrected contract and current pinned source evidence in the spec, design, QA, and gate; do not treat prior optional-origin or old songshan-source evidence as current. (Current expanded snapshot is 26,485,976 bytes, SHA-256 `9db94dd723445fb45e73a77dca4ee4a74783af26e04794fc3fc9d5f63aa0f868`; old `faae4ffd...` remains historical.)
- [x] 17. Run focused direction tests plus broad regression and isolated browser smoke; do not claim biological validation. (209 Python tests, 64 web tests, typecheck/lint/format/build, and 24 isolated desktop/mobile browser scenarios passed.)
