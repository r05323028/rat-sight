# Quality assurance — optimize-map-interaction-and-animated-simulation

## Scope

This record covers the map inspector, the MapLibre source/layer lifecycle, GSAP route reveal and walker playback, animation controls, and the measured rendering comparison. It does not change the movement model, the simulation API contract, source provenance, eligibility policy, or OpenSpec acceptance.

All commands were run from `/Users/seanchang/rat-sight` on 2026-10-27 against HEAD `e90ae90` plus this change's uncommitted working tree.

## Automated checks

| Check | Command | Result |
| --- | --- | --- |
| Web unit tests | `corepack pnpm --filter @ratsight/web exec vitest run` | 4 files, 81 tests passed |
| Python tests | `make test-py` | 230 passed in 81.29 s |
| Web tests via make | `make test-js` | 4 files, 81 tests passed |
| Typecheck | `make typecheck` | tsc 0 errors; basedpyright 0 errors, 0 warnings |
| Lint | `make lint` | eslint clean; ruff `All checks passed!` |
| Formatting | `make format-check` | Prettier clean; 421 Python files already formatted |
| Production build | `make build` | Next.js 16.4.2 compiled successfully, 3 static pages |
| Browser smoke | `bash scripts/geospatial_smoke.sh` | 30 passed: 20 citizen-origin (10 desktop, 10 mobile) plus 10 cross-suite |
| OpenSpec validation | `openspec validate optimize-map-interaction-and-animated-simulation --strict` | Change is valid |
| Quality gate | `make openspec-gate CHANGE=optimize-map-interaction-and-animated-simulation` | See `gate.json` and the gate section below |

The browser smoke runs a disposable PostGIS database, the real FastAPI process, the pinned local OSM graph, and the real Next.js app. Only the external basemap style is stubbed. It includes the new workflows:

- Desktop and mobile inspection beside the map with a non-intersecting desktop card and a compact post-run mobile sheet.
- Preview and four playback steps without layer or source reconstruction.
- Origin change that clears the previous playback and card content.
- Keyboard-only simulation start (focus plus Enter).
- Reduced-motion mode: animation toggle off, zero animation frames after settling, static routes, and step-by-step inspection.
- Existing error paths: source-version conflict, ineligible category, missing aggregate service, missing OSM source, unresolvable cell, and missing API.

## Performance evidence

Full record: `docs/benchmarks/map-interaction-performance.json`. Harness: `apps/web/e2e/measure-map-performance.mjs`.

Environment: macOS-26.3.1-arm64, Playwright Chromium 1.64.1 at 1440x900, Next.js dev server, real FastAPI, developer PostGIS, pinned `taipei-expanded-ratdar-20261027.osm` (71,281 nodes / 208,244 directed edges), published snapshot `2026-10-26T20:53:32Z` (sha256 `eae7182b…`, 91 cells), 24 walkers / 12 steps / seed 42, selected cell `g250m:11147:49043:2026-05:sighting`.

| Metric | Before (`e90ae90`) | After | Change |
| --- | --- | --- | --- |
| Map panning frame time, p50 / p95 | 16.7 / 16.7 ms | 16.7 / 16.7 ms | unchanged (already frame-locked) |
| Map panning long tasks | 0 | 0 | unchanged |
| MapView commits during pan | 0 | 0 | unchanged |
| Aggregate requests during pan | 0 | 0 | unchanged |
| Source / layer builds on preview arrival | 13 / 23 | 0 / 0 | −100% |
| Source / layer builds during 4 playback steps | 21 / 37 | 0 / 0 | −100% |
| setData calls during 4 playback steps | 0 | 8 | playback now updates existing sources |
| Cumulative source / layer builds, full flow | 39 / 71 | 7 / 11 | −82.1% / −84.5% |
| MapView commits during 4 playback steps | 5 | 5 | unchanged |
| Preview latency | 3,113 ms | 3,170 ms | +1.8% (backend-dominated; no improvement claimed) |
| Preview payload | 1,879,247 bytes | 1,879,247 bytes | unchanged |
| Reveal animation frames in 1.2 s | 0 (feature did not exist) | 78 (~65 fps) | new capability |
| Post-GC heap, idle / simulation | 22.0 / 26.5 MB | 22.4 / 28.1 MB | +1.6 MB with animated sources |

Interpretation: panning was already vsync-locked in both builds, so this change does not claim an FPS improvement. The measured rendering win is structural: preview and playback no longer remove and recreate static MapLibre sources and layers, and a new reveal animation runs without per-frame React commits. GeoJSON processing duration was not separately instrumented in the baseline, so it is evidenced by the eliminated rebuilds rather than a before/after duration.

## Real-data versus fixture evidence

The performance run used the real published aggregate snapshot, the real API, the pinned OSM network, and the real dashboard in Chromium. It exercised marker selection, simulation start, route reveal, individual playback, and a scripted pan on one desktop viewport.

All layout, error-handling, keyboard, reduced-motion, and mobile assertions were run against the isolated synthetic aggregate fixture in the browser smoke. No mobile real-snapshot run, no Safari/Firefox run, and no production-build profiling were performed. Nothing in this record treats a fixture run as real-snapshot validation.

## UX and accessibility observations

- Desktop details live in the control rail and the browser test asserts the card's box does not intersect the map box; the map stays visually dominant.
- On mobile the inspector becomes a bottom sheet with safe-area inset, is capped below 40% of the viewport once a run exists, and leaves the playback controls reachable.
- Selecting a marker only highlights it and opens details; it never starts a simulation. Starting a run is an explicit button action and works from the keyboard.
- Context-only report categories show their explanation and a disabled simulation action; the disabled state is not a frontend-only rule (the API still rejects the request).
- Playback speed and the animation toggle are labelled in Traditional Chinese, and the speed note `模擬播放速度，非實際鼠類移動速度` is visible.
- Reduced motion defaults the animation toggle off, produces static routes, and keeps step inspection usable.
- Selected-cell details, provenance, and scientific caveats remain available in the rail/details disclosure; simulation output keeps its `SIMULATED` label and source cell identity.

Not verified: real touch-device gestures, screen-reader narration, high-contrast/forced-colors mode, and browser zoom/text scaling at 200%. These remain candidates for later accessibility work.

## Gate status

`make openspec-gate CHANGE=optimize-map-interaction-and-animated-simulation` → `RESULT: PASS` on 2026-10-27, with one non-blocking warning: `Bounded route-flow indication` is `PARTIALLY_VERIFIED` because the 24-edge cap is inspected rather than directly asserted. The change stops at Ready for Human Review and is not archived.
