# Adversarial review — optimize-map-interaction-and-animated-simulation

## Method

Attempted to break the interaction, the rendering lifecycle, and the scientific framing: popup obstruction, per-tick reconstruction, stale animation after origin changes, decorative motion that implies observation, reduced-motion regressions, memory growth, and payload/latency regressions. Evidence comes from the committed browser smoke, the unit suites, and the measured before/after runs in `docs/benchmarks/map-interaction-performance.json`.

## Findings

### FCO-MAP-001 — Details could still obscure the routes (MAJOR, RESOLVED)

The popup was replaced by a rail inspector on desktop and a safe-area bottom sheet on mobile. The browser test asserts the desktop card box does not intersect the map box, and on mobile asserts the post-run sheet stays under 40% of the viewport height while playback remains reachable. The selected origin stays highlighted through the existing selected-origin layer.

### FCO-MAP-002 — Playback still rebuilds static geometry (MAJOR, RESOLVED)

Measured on the same stack: four playback steps went from 37 layer builds and 21 source builds to 0 and 0, using 8 `setData` calls. Preview arrival went from 23/13 to 0/0. Cumulative builds for the full flow fell from 71/39 to 11/7. The test also asserts the counters do not change across two steps.

### FCO-MAP-003 — A stale animation could survive an origin change or unmount (MAJOR, RESOLVED)

All reveal, walker, and flow tweens are killed in effect cleanup; preview/mode changes re-run the effects; flow is cleared on drag, hidden tab, reduced motion, disabled animation, or aggregate mode exit. The browser workflow changes origin and asserts the playback region disappears and the card shows only the new cell. No stale route or playback control remains.

### FCO-MAP-004 — Animation could imply observed rodent movement (MAJOR, RESOLVED)

The reveal follows the returned trajectory geometry and the line gradient grows from the origin; the walker interpolates along the returned polyline by arc length. The interface labels the result `SIMULATED`, keeps the source cell identity, and states `模擬播放速度，非實際鼠類移動速度`. Flow markers are bounded and bidirectional, not a one-way migration claim. No model or provenance classification changed.

### FCO-MAP-005 — Preview latency and payload remain large (MAJOR, OPEN)

Preview latency was 3,113 ms before and 3,170 ms after, with an unchanged 1,879,247-byte payload for this cell/configuration. The frontend change does not address response size or backend compute. This is outside the declared scope (no API or model change) but remains the dominant wait in the workflow and should be handled in a separate backend change if it becomes a product problem.

### FCO-MAP-006 — Flow indication covers only a bounded subset (MINOR, OPEN)

Flow markers are limited to the first 24 aggregate edges, two markers each, to keep the effect cheap. The visualization is therefore illustrative of direction, not proportional coverage of all simulated edges. This is intentional and documented in the design, but a viewer could over-read the subset. The legend and `SIMULATED` framing remain the mitigation.

### FCO-MAP-007 — Measurement coverage is narrow (MINOR, OPEN)

Before/after numbers come from one machine, one headless Chromium build, one viewport, one selected cell, and development servers. Panning was already frame-locked, so no FPS gain is claimed. Safari, Firefox, low-end hardware, zoom gestures, mobile drag performance, and production builds were not measured. Reduced motion was verified through Playwright media emulation and mobile through a mobile viewport project, not physical devices.

## Decision

PASS_WITH_WARNINGS. No BLOCKING finding remains. The two open findings are a scoped backend latency/payload limitation and documented measurement/visualization limits; neither invalidates the delivered interaction or the measured rendering improvement. Stop at Ready for Human Review; do not archive.
