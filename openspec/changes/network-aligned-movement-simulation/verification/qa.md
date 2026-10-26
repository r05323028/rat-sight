# QA verification — network-aligned movement simulation

Independently executed by `verification.qa@rat-team`, 2026-10-23 17:30–17:45 CST (09:30–09:45Z).
Read-only on code: no implementation file was edited by QA. Task from orchestration-lead (m01047,
m01055). Runtime under test: web `http://127.0.0.1:3000`, API `http://127.0.0.1:8000` (lead-provided),
plus an isolated QA API on `127.0.0.1:8002` against the read-only profile DB on 54330.

## IMPORTANT — moving target

`packages/geo/src/ratsight_geo/osm.py` changed underneath the run at 17:38 CST: `edge_id` for reverse
edges became `f"{source_id}:reverse"` (file 3.5K → 4.0K). Everything below was re-run after that edit.
Verified fingerprints at time of final run:

```
75daaf2c25f2  packages/geo/src/ratsight_geo/osm.py
8c426640fc1c  packages/simulation/src/ratsight_simulation/movement/random_walk.py
10480a3a5ee5  services/api/src/ratsight_api/application/simulation_preview.py
321977806d5b  apps/web/src/components/map-view.tsx
```

The pre-edit revision had non-unique `edge_id` across directions (86 duplicate ids of 249 edges);
the frontend aggregate filter (`apps/web/src/components/map-view.tsx`, `.find()` on `edge_id` only)
produced 17 wrong `visits` labels and 3 never-traversed edges drawn at seed 0. Re-checked after the
edit: 0 duplicate ids, 0 phantom edges. Recorded because it shows the collision class is real, not
hypothetical.

## Commands and results

| ID | Command | Result |
| --- | --- | --- |
| V-PY | `uv run pytest packages/geo/tests/test_osm.py services/api/tests/test_simulation_preview.py -q` | 4 passed |
| V-PY-ALL | `uv run pytest packages services -q` | 150 passed, **3 failed** (pre-existing, see F4) |
| V-JS | `cd apps/web && corepack pnpm exec vitest run` | 3 files / 61 tests passed |
| V-TC | `cd apps/web && corepack pnpm typecheck` | `tsc --noEmit` clean |
| V-LINT | `make lint` | eslint + ruff "All checks passed!" |
| V-OSM | `corepack pnpm exec openspec validate network-aligned-movement-simulation --strict` | valid |
| V-PROBE | `uv run python /tmp/qa-netalign-probe.py` | 17/17 PASS, 0 failures |
| V-SEED | 40-seed HTTP sweep (seeds 0–39) against `:8000` | 0 failures |
| V-BROWSER | `/tmp/qa-netalign-browser.cjs` on `:3000` | payload + labels pass, 0 console errors |

## Geometry — bends preserved

- Graph: 117 nodes, 249 directed edges from the pinned extract (`5831ea28d78c…`, 9,323 nodes /
  1,018 ways in source).
- **Every one of the 249 edge geometries is a verbatim consecutive subsequence of its source way's
  node coordinates** (0 mismatches, forward or reversed). No coordinate invented, none dropped.
- 73 edges carry ≥3 coordinates, i.e. bends exist and survive to the payload.
- Every edge geometry's first/last coordinate equals the declared source/target node coordinate (0
  mismatches) — so no edge is drawn from node-to-node when the source had bends.
- Connectivity is shared-OSM-node only; the ways split at shared nodes, and split segments keep all
  intermediate refs.

## No straight OSM shortcuts

- Payload scan for 2-coordinate edges longer than 150 m: 4 hits, all legitimate — way `432918277`
  has exactly 2 nodes in the source (203 m straight road), and `432918278:1` is a split segment
  bounded by shared nodes. Not artifacts.
- Trajectories: every step is topologically continuous (`prev.target == next.source`, 24 walkers ×
  40 seeds, 0 violations) and each step carries its own full geometry; the renderer concatenates
  with `slice(1)` so no bend is lost between steps.
- Renderer takes `edge.geometry` verbatim when present; the 2-point `[start, end]` fallback now
  applies only when `geometry` is absent, which today means only the schematic
  `taipei_synthetic_demo` area (verified: 0 edges with geometry in that payload).

## Determinism

- Same seed → byte-identical payload (in-process: `e56e1526…`, then `3fa6ebde…` after the edit;
  over HTTP at seed 42: `2ee031f8…` twice identical, 158,297 bytes each run).
- 40 seeds × 2 calls over HTTP: 40/40 reproducible.
- Geometry is seed-invariant: all 40 seeds produce the identical geometry hash; only visits change.
- `start_node = next(iter(graph.nodes))` is deterministic (XML insertion order).

## Aggregate counts

- `sum(node_visits) == walkers + sum(edge_visits)`: 312 == 24 + 288 at the default run; holds for all
  40 seeds. Arithmetic was changed from `walkers * (steps + 1)` to a real sum so early termination
  no longer inflates totals.
- `sum(edge_visits) <= walkers * steps` (288 ≤ 288); early-terminated walkers stop at dead ends
  (`terminated_early`), 7 nodes in this extract have out-degree 0.
- `trajectory_count == walkers` (24); 150 walkers → 100 rendered with `trajectory_truncated: true`.
- Max params (100 steps / 1000 walkers): HTTP 200, 1,216,038 bytes, 1.05 s, 100 trajectories,
  truncation flagged. Bounded but the cap is not surfaced in the UI (see F2).

## API

- `study_area` allowlist enforced: `"nope"` → HTTP 422 with the two valid literals.
- Provenance carries `source_type: osm_surface_network`, `source_id: taipei-songshan-20261023.osm`,
  `source_sha256: 5831ea28…`, `attribution: © OpenStreetMap contributors; ODbL 1.0`.
- Assumptions list states unitless uncalibrated weights, SIMULATED-only, surface-only connectivity,
  ODbL attribution, and that geometry is not biological evidence.
- Missing/corrupted source fails closed: `FileNotFoundError: configured OSM source is absent` and
  `ValueError: OSM source sha256 mismatch` (`packages/geo/src/ratsight_geo/osm.py`).

## Browser (`:3000`)

- OSM payload returned from the live page; bent geometry present (73/249); labels
  `合成`/`SIMULATED` visible; `OpenStreetMap` attribution visible.
- Trajectory mode selectable; 0 console errors; screenshots
  `/tmp/qa-netalign-shots/01-osm-aggregate.png`, `02-osm-with-network-reference.png`,
  `03-osm-trajectories.png`.
- Not checked in the browser: pixel-level alignment of drawn lines against the basemap (screenshot
  only), and the network-reference layer visually (checkbox label not matched by the probe).

## Findings

| ID | Severity | Finding |
| --- | --- | --- |
All three implementation findings were fixed after this QA run:

- F1: dead-end starts and zero-edge walks now terminate with safe zero edge probabilities.
- F2: the dashboard reports trajectory count and the 100-trajectory rendering cap.
- F3: source documentation now states that per-way OSM versions are not exposed by the adapter.

The independent browser limitation remains: pixel-level curved-line alignment was not verified interactively.
| F4 | MINOR (pre-existing, not this change) | `uv run pytest packages services` → 3 failures in `services/api/tests/test_rodent_reports_import.py::test_persist_import_is_idempotent_and_fail_closed`, `::test_bbox_and_time_filter_select_matching_points`, `::test_immutability_trigger_blocks_update_and_delete` — `RodentReportConflictError: fixture record identity set changed`. Cause: tests run against the shared dev DB `127.0.0.1:54329` which holds 5 rodent rows from earlier smoke runs, so the fixture identity set no longer matches. Test isolation defect, unrelated to this change (neither the importer nor these tests were touched) |

## Default and unavailable-source follow-up

- Historical QA (2026-10-23) observed `taipei_osm_songshan` as API/UI default; its OSM browser result describes pre-restoration behavior only.
- Historical OSM checks: `./scripts/fetch_taipei_osm_source.sh` verified the already provisioned pinned artifact without fetching mutable upstream data; a deliberately checksum-mismatched artifact returned HTTP 503 with `SOURCE_NETWORK_UNAVAILABLE`, expected path, and provisioning documentation. Pinned artifact was preserved.
- Owner later chose restoring compatibility default `taipei_synthetic_demo` (superseded 2026-10-26, see next bullet). API unit and HTTP-route regressions at that time asserted an omitted study area defaulted to synthetic without calling the OSM loader.
- 2026-10-26 owner reversal to OSM-first defaults: `SimulationPreviewRequest.study_area` and the Dashboard selection now default to `taipei_osm_songshan`, so an omitted `study_area` follows the pinned surveyed network and multi-vertex source geometry. `taipei_synthetic_demo` remains explicitly selectable, its geometry-less links are drawn dashed on a dedicated schematic layer, and a 示意拓撲 note states the network connects nodes with straight lines rather than road geometry. A missing or mismatched pinned artifact still returns `SOURCE_NETWORK_UNAVAILABLE`; no schematic fallback is substituted. Regressions: `cd services/api && uv run pytest -q` → **150 passed**; `cd apps/web && npx vitest run` → **84 passed**; `npx tsc --noEmit` clean. Live `POST /api/v1/simulations/preview {}` returned `source_type: osm_surface_network`, 249 edges all with geometry (73 multi-vertex), and 24 trajectories.
- 2026-10-26 verification: `uv run pytest services/api packages/geo packages/simulation -q` → **163 passed**; `cd apps/web && npm test -- --run` → **79 passed**; `npm run typecheck`, `npm run lint`, and Python Ruff checks passed. Touched Dashboard files pass targeted Prettier.
- Browser workflow was not rerun after default restoration. Prior OSM browser evidence does not prove current synthetic initial-selection browser behavior; automated tests cover current default. Pixel-level basemap alignment remains unverified. Workspace-wide Prettier check still reports 12 files outside this task.

## Limitations

- Street-network *alignment with real streets* is proven only against the pinned OSM extract's own
  geometry; the extract is a 0.004°×0.004° bbox around Songshan, not a city inventory.
- No claim about rodent street use, prevalence, risk, hotspots, or interventions is supported or
  tested. Movement weights are unitless placeholders.
- Underground/stormwater connectivity is untouched and, per the spec scenario, no transition is
  inferred from geometric intersection — verified only by inspection of the graph construction
  (`load_osm_surface_graph` reads `highway` ways only; stormwater is never loaded), not by an
  executable test.
- Single machine, upstream `next dev` on `:3000`; no production build was exercised for this change.
- `verification/gate.json` for this change was not written: the gate also requires
  `verification/code-review.md` and a change-root `adversarial-review.md`, which are reviewer
  artifacts, not QA's. Gate stays blocked until those exist.
