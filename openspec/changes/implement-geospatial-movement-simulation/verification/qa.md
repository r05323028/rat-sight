# QA verification

## Automated checks

- Full `uv run pytest services/api packages/geo packages/simulation -q` → **189 passed, 6 pre-existing shared-database importer conflicts**.
- Targeted `uv run pytest services/api/tests/test_api.py services/api/tests/test_simulation_preview.py packages/simulation/tests -q` → **31 passed**.
- Simulation requests now require explicit `study_area`; omitted requests return HTTP 422. Explicit `taipei_osm_songshan` returns OSM provenance, explicit `taipei_synthetic_demo` returns `synthetic_fixture`, and a missing extract returns 503 `SOURCE_NETWORK_UNAVAILABLE`.
- `cd apps/web && npm test` → **91 passed**.
- `cd apps/web && npm run typecheck`, `cd apps/web && npm run lint`, Ruff on affected Python packages, and targeted Prettier checks for Dashboard files → clean.
- Workspace-wide `cd apps/web && npm run format:check` still reports 12 files outside this task (`.impeccable` artifacts, `DESIGN.md`, `tsconfig.json`).
- `npx playwright test e2e/dashboard.spec.ts` with isolated mocked services → **10 passed** (desktop/mobile).
- `openspec validate implement-geospatial-movement-simulation --strict` → valid.

## Real isolated runtime

QA used disposable databases and API/web pairs, without touching shared databases. Populated and empty environments were checked at 1440×900 and 390×844.

- API returned explicit default/user origin metadata and echoed `parameters.origin_node_id`.
- Explicit origin changed trajectories; unknown origin returned HTTP 422 `ORIGIN_NODE_NOT_IN_GRAPH` without snapping.
- `step_index` was zero-based and contiguous.
- Pointer and touch origin selection, pending-origin disclosure, play/pause, next, reset, trajectory selection, termination copy, and truncation disclosure passed.
- Empty environment remained honest while simulation still ran; no infrastructure claim was shown.
- Teardown left no QA listeners or databases.
- Municipal Analyst PASS: QA-owned `127.0.0.1:3086` → API `8005`; origin pending state, step playback, `step_index`, reachability/unsampled disclosure, truncation, and non-biological safeguards passed with no UX finding.

## Source hash reconciliation

- Current local snapshot `$HOME/.local/share/ratsight/network/taipei-songshan-20261023.osm` hashes to `faae4ffd1bd42e57871bdedbfdcc6e82b3324a458db95034d4ec40f0a019e67e` with `shasum -a 256`. This matches `EXPECTED_SHA256` in `packages/geo/src/ratsight_geo/osm.py`, `docs/infrastructure/taipei-osm-network-source.md`, and `openspec/changes/network-aligned-movement-simulation/verification/source.md`; OSM loader tests passed in the Python suite.
- `openspec/changes/network-aligned-movement-simulation/verification/qa.md` records prefix `5831ea28d78c…` for an earlier run but provides no full digest or separately identified snapshot. Its `verification/source.md` says API response was re-pinned after an earlier snapshot changed. Different historical bytes are plausible, but exact prior bytes remain **UNVERIFIED**.
- Treat `5831ea28d78c…` as historical/unverified, not current source identity. Current artifact checksum is verified; no live OSM fetch occurred. Checksum does not establish rodent-use evidence or model validity.

## Findings and limits

- **F1 resolved (2026-10-27):** stormwater list accessible names now begin with the visible pipe label and append the stable segment ID. Focused dashboard coverage and isolated desktop/mobile `real-stormwater.spec.ts` checks assert the visible-name/accessible-name contract. No axe dependency was added; a full axe scan remains unverified.
- **F2 resolved:** playback trajectory select was below 24px at mobile width; CSS now gives it a 44px minimum height.
- Failed preview runs now clear prior trajectory output, preventing stale results after an origin error.
- Preview now reports topology reachability and explicit termination reasons; UI distinguishes disconnected/unsampled graph areas without biological inference.
- Screen reader, hardware touch, forced-colors, 200% zoom, and pixel-level trajectory alignment remain unverified.
- One playback unit probe was flaky once in nine runs; no reproduction. Follow-up may replace timer reliance with fake-clock assertions.

## 2026-10-27 corrective addendum — OSM direction semantics and current regression

- `/Users/seanchang/rat-sight/packages/geo/src/ratsight_geo/osm.py` now retains `oneway` as vehicle metadata instead of using it to decide movement direction. Candidate movement edges are bidirectional; reverse edges carry reversed source geometry; topology still comes only from shared OSM nodes, so visual/grade-separated crossings remain disconnected.
- Added `test_vehicle_oneway_metadata_does_not_remove_reverse_movement` and `test_visual_crossings_without_shared_osm_nodes_remain_disconnected` in `/Users/seanchang/rat-sight/packages/geo/tests/test_osm.py`; focused tests pass and the pinned-source checksum is unchanged.
- Current pinned expanded snapshot is `/Users/seanchang/.local/share/ratsight/network/taipei-expanded-ratdar-20261027.osm`, 26,485,976 bytes, SHA-256 `9db94dd723445fb45e73a77dca4ee4a74783af26e04794fc3fc9d5f63aa0f868`. The old songshan `faae4ffd...` and prior `5831ea28...` evidence are historical, not current-source evidence.
- The earlier optional-origin/default wording in this change is superseded: public OSM requires an eligible `origin_cell_id`; only the isolated synthetic demo retains explicit graph/fixture origins.
- Final regression after all code/test changes: `make test-py` 209 passed in 103.69s; `make test-js` 64 passed; typecheck, lint, format-check, and build passed; `bash scripts/geospatial_smoke.sh` passed 24 isolated desktop/mobile scenarios: 14 citizen-origin (including playback, origin switching, out-of-order, aggregate/simulation/OSM failures, unresolvable cell, refreshed-source disappearance), 2 empty fixture, and 8 admin/stormwater.
- Blocker follow-up (2026-10-27): F1 and the synthetic-seed reprojection fix were verified by 209 Python tests, 64 web tests, typecheck/lint/format/build, and the 24-scenario isolated browser smoke. The seed produced a valid 250 m EPSG:4326 cell with no Shapely deprecation warning.
- Task 12 remains open: Municipal Analyst re-evaluation is PASS, but Public Health/Modeler/Reviewer sign-off and formal CR-008 provenance authentication are pending. The gate now fails on incomplete required tasks. No biological validation is claimed.

Verdict: **PASS WITH WARNINGS**, not ready for human acceptance until task 12 and independent review close.
