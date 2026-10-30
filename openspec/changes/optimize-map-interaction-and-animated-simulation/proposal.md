# Optimize map interaction and animated simulation

## Why

The simulation workspace has three compounding problems. The citizen-report detail card is a
MapLibre popup anchored to the selected cell, so it covers the origin, nearby roads, and the
simulated routes. Every playback tick removes and re-adds all simulation and network sources and
layers, and the aggregate layer rebuilds its features with a `preview.edges.find()` inside loops,
so selection and stepping pay full reconstruction cost. Simulated routes appear at once and do not
communicate direction or progress, so the movement result reads as a static tangle.

## What Changes

- Move the citizen-report details out of the map into the control rail on desktop and into a
  collapsible bottom sheet on mobile, with the selected marker highlighted and an explicit
  simulation action. Context-only report categories stay inspectable but cannot start a run.
- Split MapLibre rendering into stable static sources/layers and dynamic presentation state. A
  preview is transformed once into an index (network geometry, simulated edges, walker step ends,
  schematic fallback), then applied through `setData`, `setFilter`, and layout/paint updates.
- Reveal simulated routes progressively along the returned trajectory geometry, add a bounded
  bidirectional flow indication, and animate the selected walker position along its polyline while
  step playback, pause, seek, and reset keep working.
- Add playback speed (0.5x, 1x, 2x) and an animation toggle, defaulting off under
  `prefers-reduced-motion`, and state that playback speed is not real rodent speed.
- Measure the before/after behavior on one machine and record the evidence, instead of asserting
  smoothness.

## Impact

- Affected specs: new `simulation-map-visualization` capability delta.
- Affected code: `apps/web/src/components/map-view.tsx`, `apps/web/src/components/dashboard.tsx`,
  `apps/web/src/app/globals.css`, `apps/web/src/lib/simulation-geometry.ts`,
  `apps/web/src/lib/use-prefers-reduced-motion.ts`, component tests, and
  `apps/web/e2e/real-citizen-origin.spec.ts`.
- Dependency: `gsap` (animation timing only); no backend, API contract, model, provenance, or
  database change.
- Compatibility: the simulation request/response contract, classifications, suppression, and
  source-version rules are unchanged. Synthetic fixtures remain visually distinct.

## Out of Scope

- Changing the movement model, biological assumptions, or simulation outputs.
- A backend animation service, streaming transport, worker queue, or new database.
- A dashboard redesign beyond the inspection surface and playback controls.
