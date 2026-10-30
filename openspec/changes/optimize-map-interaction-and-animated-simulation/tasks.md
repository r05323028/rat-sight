# Tasks

## Specification and design

- [x] 1. Inspect the current MapView lifecycle, popup card, playback effect, viewport query debounce, dashboard state, and browser smoke contract.
- [x] 2. Write the delta requirements for inspection, stable layers, reveal, flow, walker playback, animation controls, and measured performance.

## Implementation

- [x] 3. Replace the map popup with a control-rail inspector on desktop and a collapsible safe-area sheet on mobile, keeping marker highlight, explicit run, close, ineligible explanation, and source details.
- [x] 4. Restructure `apps/web/src/components/map-view.tsx` so static sources and layers are created once per style load and updated through `setData`, filters, and layout properties.
- [x] 5. Build a per-preview cache for network features, aggregate edges, walker step ends, and the schematic fallback, removing repeated edge searches from render paths.
- [x] 6. Add GSAP-driven route reveal, bounded bidirectional flow, and walker position interpolation along the returned polyline without per-frame React state.
- [x] 7. Add playback speed, animation toggle, reduced-motion default, and the `模擬播放速度，非實際鼠類移動速度` note to the dashboard playback controls.
- [x] 8. Update styling for the inspector, sheet, playback settings, and compact post-run state without redesigning the dashboard.

## Verification

- [x] 9. Extend component tests for rail inspection, context-only reports, speed/toggle propagation, and reduced-motion default; update MapLibre lifecycle tests to assert `setData` use instead of layer reconstruction.
- [x] 10. Extend the committed browser smoke with a non-obstructive inspection and animation workflow on desktop and mobile.
- [x] 11. Run the geometry unit tests, web unit tests, typecheck, lint, formatting, build, and `bash scripts/geospatial_smoke.sh`.
- [x] 12. Measure pan frames, commits, rebuild counts, payload, latency, animation frames, and heap against the baseline on the same stack and record the report under `docs/benchmarks/`.
- [x] 13. Run `openspec validate` and the quality gate, then stop at Ready for Human Review without archiving.

Status: implementation and verification are complete. The change is Ready for Human Review; it does
not modify the movement model, API contract, data classifications, or approval workflow.
