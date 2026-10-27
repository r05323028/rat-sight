# QA

Engineering-slice result before 2026-10-27: PASS_WITH_WARNINGS for synthetic-only behavior. Current disposition: targeted owner-directed real-cell verification passes, including uniform seeding across multiple strictly in-cell nodes, but the full change remains BLOCKED pending source/legal/privacy terms, scientific/CRS/ambiguity approvals, independent review, and an approved real-data workflow; not Ready for Human Review.

- `uv run pytest packages/simulation/tests/test_random_walk.py services/api/tests/test_simulation_preview.py services/api/tests/test_citizen_report_aggregates_api.py services/api/tests/test_citizen_report_aggregates_import.py -q`: 55 passed; covers synthetic resolver invalid-ring, strict-boundary, deterministic, and CRS metadata behavior plus aggregate suppression/API contracts.
- `cd apps/web && corepack pnpm exec vitest run src/components/dashboard.test.tsx src/components/map-view.test.tsx`: 80 passed.
- `uv run basedpyright packages/simulation/tests/test_random_walk.py services/api/tests/test_simulation_preview.py`: 0 errors, 0 warnings, 0 notes.
- `uv run ruff check packages/simulation/tests/test_random_walk.py services/api/tests/test_simulation_preview.py`: no issues; `uv run ruff format --check packages/simulation/tests/test_random_walk.py services/api/tests/test_simulation_preview.py`: 2 files already formatted.
- New dashboard tests cover explicit synthetic fixture request, control disable/reset outside the synthetic study area, and aggregate-cell selection remaining display-only.
- `cd apps/web && corepack pnpm run typecheck`: passed.
- `cd apps/web && corepack pnpm exec eslint src/components/dashboard.tsx src/components/dashboard.test.tsx`: passed.
- `cd apps/web && corepack pnpm exec prettier --check src/components/dashboard.tsx src/components/dashboard.test.tsx`: passed.
- `openspec validate citizen-report-driven-simulation-origins`: passed.
- `make openspec-gate CHANGE=citizen-report-driven-simulation-origins`: BLOCKED (Make exit code 2; gate result `BLOCKED`) because CR-ORIGIN-001..004 remain `BLOCKING`/`OPEN` and required sensitive-data approval is `PENDING` (missing `verification/acceptance.md`, approver, and reference).

## 2026-10-27 addendum — owner-directed real-cell origin

- Added explicit OSM aggregate-cell origin selection, strict in-cell API execution, candidate-count/resolver provenance, fail-closed errors, and marker-vs-cell UI separation.
- `uv run pytest services/api/tests/test_simulation_preview.py -q`: 19 passed.
- `corepack pnpm --filter @ratsight/web test src/components/dashboard.test.tsx`: 46 passed.
- `make test-js`: 74 passed (3 files).
- `make test-py`: 189 passed in 69.70s.
- `make typecheck`: passed; `make lint`: passed.
- Targeted Prettier check for `apps/web/src/components/dashboard.tsx` and `apps/web/src/components/dashboard.test.tsx`: passed after formatting. Full `make format-check` remains non-clean because unrelated `.impeccable/*` files fail Prettier.
- `make openspec-gate CHANGE=citizen-report-driven-simulation-origins`: BLOCKED because CR-ORIGIN-001..004 remain `BLOCKING`/`OPEN` and required sensitive-data approval is `PENDING`.

## 2026-10-27 addendum 2 — uniform multi-node cell origin

- Root cause of the one-node-only limitation: the previous pinned 0.004° Songshan extract had zero nodes in all 91 published cells. The then-current pinned snapshot `/Users/seanchang/.local/share/ratsight/network/taipei-songshan-ratdar-20261026.osm` (SHA-256 `e92235f1a518aa84a6194eaec33f70ea636ca9353d54a5b59d36592f2723255b`, bbox `121.5260,25.0245,121.5370,25.0340`, retrieved `2026-10-26T18:55:11Z`) contains 1,243 highway-graph nodes and 3,233 edges; the nearest published cell `g250m:11143:49036:2026-05:sighting` contains 83 eligible nodes.
- `resolve_origin_cell` now fails closed only at zero candidates, uses `strict-in-cell-v1` for one candidate, and returns every strictly in-cell node under `uniform-in-cell-v1` for multiple candidates. `run_weighted_random_walk` accepts `start_nodes` and chooses each walker start uniformly with the seeded RNG. Reachability is the union over all candidate origins. Counts still never become walker counts or weights.
- `uv run pytest packages/geo/tests/test_osm.py -q`: 3 passed after the test was changed to load `DEFAULT_OSM_SOURCE` instead of a hardcoded old path; the first full run had 2 failures from that stale path and was rerun clean.
- Targeted: `uv run pytest packages/simulation/tests/test_random_walk.py -q`: 17 passed; `uv run pytest services/api/tests/test_simulation_preview.py -q`: 20 passed; `corepack pnpm --filter @ratsight/web test src/components/dashboard.test.tsx`: 46 passed.
- Full: `make test-py`: 191 passed in 80.38s; `make test-js`: 74 passed (3 files); `make typecheck`: passed; `make lint`: passed.
- Live probe against the current API on `http://127.0.0.1:8000`: `POST /api/v1/simulations/preview` with `study_area=taipei_osm_songshan`, `origin_cell_id=g250m:11143:49036:2026-05:sighting`, 3 walkers, 4 steps, seed 42 returned 200; origin representative `node_id=11380781487`, 83 `node_ids`, `cell_candidate_count=83`, `cell_resolver_version=uniform-in-cell-v1`; reachability 1,217/1,243 nodes and 3,201/3,233 edges; all 3 walkers completed 4 steps with first sources `11385111759`, `632258928`, `632259392`.
- A second live probe with 30 walkers and seed 7 returned 200; 28 distinct first sources, all 30 first sources contained in the 83 `node_ids`, every walker completed 2 steps, and all outputs were classed `SIMULATED`. This confirms seeding is spread across the selected cell rather than pinned to the representative node.
- `openspec validate citizen-report-driven-simulation-origins`: passed.
- `make openspec-gate CHANGE=citizen-report-driven-simulation-origins`: still BLOCKED because CR-ORIGIN-001..004 remain `BLOCKING`/`OPEN` and required sensitive-data approval is `PENDING`.

## 2026-10-27 addendum 3 — focused aggregate-cell card

- Added marker click focus with a React detail card over the map, marker highlight, aggregate-only details (cell, month, report type, published count, 250 m centroid caveat, `UNVERIFIED`, attribution), and an explicit card action that runs the focused cell.
- Focus alone does not set `origin_cell_id`/`origin_node_id` and does not send a preview request. The card action sends `origin_cell_id` without `origin_node_id`; the shared request builder keeps the main run button on the same contract. Counts remain non-weights and outputs remain `SIMULATED`.
- Updated the stale advanced-control helper text to describe multi-node uniform seeding instead of the obsolete one-node-only rule.
- `corepack pnpm --filter @ratsight/web test src/components/map-view.test.tsx src/components/dashboard.test.tsx`: 70 passed.
- `make test-js`: 77 passed (3 files).
- `make typecheck`: passed; `make lint`: passed.
- Targeted Prettier check for `apps/web/src/components/dashboard.tsx`, `apps/web/src/components/dashboard.test.tsx`, `apps/web/src/components/map-view.tsx`, `apps/web/src/components/map-view.test.tsx`, and `apps/web/src/app/globals.css`: passed after formatting `dashboard.test.tsx`.
- `openspec validate citizen-report-driven-simulation-origins`: passed; `git diff --check`: clean.
- Browser/desktop interaction against the live API remains unverified, so task 12 stays open.

## 2026-10-27 addendum 4 — expanded 91-cell coverage and local map subset

- Root cause of the reported `g250m:11155:49017:2026-05:sighting` zero-candidate failure was the then-pinned OSM bbox ending at `121.5370` E; that cell lies about 600 m east of the old coverage. Resolver fail-closed behavior was correct.
- New pinned snapshot `/Users/seanchang/.local/share/ratsight/network/taipei-expanded-ratdar-20261027.osm`: 26,485,976 bytes, SHA-256 `9db94dd723445fb45e73a77dca4ee4a74783af26e04794fc3fc9d5f63aa0f868`, coverage `EPSG:4326 bbox 121.2786025,24.9821164,121.6725037,25.1249122`, OSM base timestamp `2026-10-27T13:20:28Z`. It was fetched with 30 clustered 500 m-buffered Overpass bboxes around the published cells and contains 139,865 raw nodes / 43,031 ways, yielding 71,281 graph nodes / 185,503 edges / 387 weak components.
- All 91 cells in the current aggregate dataset resolve against the new graph: 91/91, 0 missing; candidate min 3, median 60, max 286. The reported cell now resolves with 61 candidates; representative `2528739033`.
- The preview returns a disclosed 750 m `local_reference` map subset while simulation and reachability use the full graph. Live POST for the reported cell (3 walkers, 4 steps, seed 42) returned 200: origin count 61, `uniform-in-cell-v1`, reachability 54,504/71,281 nodes and 143,494/185,503 edges, 387 components, `sampled_nodes=11`, visualization 2,128 nodes / 5,263 edges versus full totals, and first sources `2528872778`, `7578489888`, `7723490408` all in the origin node list. All trajectories were `SIMULATED`.
- `uv run pytest services/api/tests/test_simulation_preview.py -q`: 20 passed. The API tests now assert that map arrays are a local subset, while reachability and visualization totals match the full graph.
- `corepack pnpm --filter @ratsight/web test src/components/dashboard.test.tsx`: 49 passed, including the full-model-totals-over-local-subset label.
- Full checks: `make test-py` 191 passed in 99.61s; `make test-js` 78 passed (3 files); `make typecheck` passed; `make lint` passed after fixing import order in `simulation_preview.py`; targeted Prettier passed; `openspec validate citizen-report-driven-simulation-origins` passed; `git diff --check` clean.
- Coverage remains a bounded engineering artifact, not an approved CRS/coverage policy. Task 12's approved browser workflow, independent review, source/privacy/scientific approvals, and final acceptance remain open; the gate remains BLOCKED.

Limits: the 2026-10-27 activation, including uniform seeding across multiple in-cell nodes, is a recorded project-owner override, not legal or scientific approval. Raw-data ingestion and redistribution remain disabled; approval tasks 3–5, approved CRS/coverage/ambiguity and report-category semantics, independent QA/scientific/analyst signoff, and an approved desktop/mobile API/browser workflow remain open. The representative node is the first sorted candidate, not an observed origin. Aggregate counts remain `UNVERIFIED` and are not animal observations or simulation outcomes. The gate remains BLOCKED.