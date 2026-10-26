# QA verification

## Automated checks

- `uv run pytest services/api packages/geo packages/simulation -q` → **171 passed**.
- Public route regression sends `{}` to `/api/v1/simulations/preview`; response defaults to `taipei_osm_songshan` with `osm_surface_network` provenance (supersedes the earlier synthetic-default assertion, reversed 2026-10-26). The explicit `taipei_synthetic_demo` request still returns `synthetic_fixture`, and a missing extract returns 503 `SOURCE_NETWORK_UNAVAILABLE`.
- `cd apps/web && npm test` → **87 passed**.
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

## Source hash reconciliation

- Current local snapshot `$HOME/.local/share/ratsight/network/taipei-songshan-20261023.osm` hashes to `faae4ffd1bd42e57871bdedbfdcc6e82b3324a458db95034d4ec40f0a019e67e` with `shasum -a 256`. This matches `EXPECTED_SHA256` in `packages/geo/src/ratsight_geo/osm.py`, `docs/infrastructure/taipei-osm-network-source.md`, and `openspec/changes/network-aligned-movement-simulation/verification/source.md`; OSM loader tests passed in the Python suite.
- `openspec/changes/network-aligned-movement-simulation/verification/qa.md` records prefix `5831ea28d78c…` for an earlier run but provides no full digest or separately identified snapshot. Its `verification/source.md` says API response was re-pinned after an earlier snapshot changed. Different historical bytes are plausible, but exact prior bytes remain **UNVERIFIED**.
- Treat `5831ea28d78c…` as historical/unverified, not current source identity. Current artifact checksum is verified; no live OSM fetch occurred. Checksum does not establish rodent-use evidence or model validity.

## Findings and limits

- **F1 pre-existing:** stormwater list accessible names do not start with visible segment IDs; axe reports `label-content-name-mismatch`. Not caused by origin/playback.
- **F2 resolved:** playback trajectory select was below 24px at mobile width; CSS now gives it a 44px minimum height.
- Failed preview runs now clear prior trajectory output, preventing stale results after an origin error.
- Preview now reports topology reachability and explicit termination reasons; UI distinguishes disconnected/unsampled graph areas without biological inference.
- Screen reader, hardware touch, forced-colors, 200% zoom, and pixel-level trajectory alignment remain unverified.
- One playback unit probe was flaky once in nine runs; no reproduction. Follow-up may replace timer reliance with fake-clock assertions.

Verdict: **PASS WITH WARNINGS**, ready for human review only.
