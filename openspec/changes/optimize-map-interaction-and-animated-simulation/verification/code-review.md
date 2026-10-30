# Code review — optimize-map-interaction-and-animated-simulation

## Scope

Reviewed the working-tree diff for `apps/web/src/components/map-view.tsx`, `dashboard.tsx`, `globals.css`, `lib/simulation-geometry.ts`, `lib/use-prefers-reduced-motion.ts`, the component/unit tests, the browser spec, and the measurement harness. Backend, model, and data files are untouched. Baseline: `e90ae90`.

## Findings

### CR-MAP-001 — Diagnostic telemetry stays in production markup (MINOR, OPEN)

`map-view.tsx` publishes a JSON summary of render/commit/build counters on `data-map-perf` in every environment. The payload is small and written only when counters change, but it is diagnostic state in the DOM. Acceptable for this change because it backs the measured acceptance evidence; a follow-up can restrict it to a measurement flag if it becomes noise. Residual risk: negligible.

### CR-MAP-002 — Baseline timing required a local instrumentation patch (MINOR, OPEN)

The committed harness reads `data-map-perf`, which HEAD did not expose. Reproducing the before column therefore needs the counters patched into the older MapView, as documented in `qa.md`. The after column is reproducible as committed. This limits one-command baseline reproduction but does not affect the implementation.

### CR-MAP-003 — Reveal relies on MapLibre line-gradient support (MINOR, OPEN)

The aggregate reveal animates `line-gradient` with `lineMetrics: true`; the schematic fallback animates opacity instead. MapLibre GL JS 6.14 supports both, and the browser smoke exercises the real renderer, but a style reload or a future renderer downgrade could drop the gradient. The code re-applies paint state after `styledata`, and the fallback stays visible, so the failure mode is a missing reveal rather than a blank route.

### CR-MAP-004 — Walker tween writes the endpoint twice on the final frame (INFO, RESOLVED)

The playback effect previously set the walker to the destination immediately and then started the segment tween, which could snap on the first frame. The final write is now guarded by `walkerAnimating`; the browser workflow advances steps and the unit test asserts the traversed path and walker source data.

## Checks performed

- No new dependency except `gsap`; no backend, API schema, model, or data-policy change.
- Static sources/layers are created behind `getSource`/`getLayer` guards and updated with `setData`, `setFilter`, `setLayoutProperty`, and paint properties.
- GSAP tweens are killed in effect cleanup and on preview/mode changes; no tween writes React state per frame.
- Flow is bounded to 24 aggregate edges with two markers each and is cleared on drag, hidden tab, disabled animation, or reduced motion.
- Geometry helpers are pure and unit-tested for arc-length interpolation, slicing, and flow points.
- Error paths preserve the previous contract and Traditional Chinese messages.

## Decision

PASS_WITH_WARNINGS. The three open MINOR findings are documented limitations, not defects blocking review. No unresolved MAJOR or BLOCKING code finding.
