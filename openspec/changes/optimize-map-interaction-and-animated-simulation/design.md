# Design

## D1: Inspector outside the map canvas

The detail card moves from a MapLibre popup into the control rail (`citizen-inspector`) on desktop
and into a fixed bottom sheet on narrow viewports, using existing card styles. Selection still
highlights the marker through a filter (`selectedCitizenCellKey`), while the card shows report type,
month, published count, uncertainty, attribution, and source version. Marker focus never runs a
simulation; the run action remains explicit. The sheet collapses to heading plus status once a
preview exists so playback controls stay reachable.

## D2: Stable MapLibre layer identities

`map-view.tsx` creates network, simulated-edge, trajectory, walker, flow, step, origin, boundary,
stormwater, and citizen sources/layers once per style load behind `getSource`/`getLayer` guards.
Data changes call `setData`; selection uses `setFilter`; visibility uses `setLayoutProperty`. The
playback effect never removes or re-adds a layer. A style reload recreates the set; teardown removes
the map. This is what removes playback and selection churn from the render path.

## D3: One preview transform, then indexed views

`buildPreviewCache()` runs when the preview object identity changes. It produces network features,
simulated aggregate features with `visits` and `source_id`, a walker map with step-end vertex
indexes, and the schematic fallback. Aggregate mode no longer calls `preview.edges.find()` per
feature; trajectory mode slices the walker polyline by cached step ends. React state changes only
touch visibility and presentation, so stepping does not rebuild GeoJSON.

## D4: GSAP drives presentation, React owns controls

GSAP tweens write numeric progress into refs and then update MapLibre sources/paint properties. They
do not call React state setters per frame. React state remains for user-visible playback state
(step, mode, playing, speed, animation toggle). Tweens are killed when the preview, mode, walker, or
selection changes, on unmount, and when the map is removed. Flow markers pause while the user drags
the map and when the document is hidden.

## D5: Animation techniques

- Reveal: a GSAP tween drives a line-gradient stop on the simulated layer (with line metrics),
  growing from the origin; schematic fallback edges fade in instead of drawing straight roads.
- Flow: a bounded set of at most 24 simulated edges carries two small markers each, moved by arc
  length over the edge geometry with a repeating phase; direction follows the simulated traversal.
- Walker: the selected walker's polyline is interpolated by arc length (`pointAtFraction`), with the
  traversed prefix drawn on top of a muted upcoming path. The marker is a position indicator, not
  an animal rendering.

## D6: Reduced motion and speed

`usePrefersReducedMotion` uses `useSyncExternalStore` over the media query. Reduced motion defaults
the animation toggle off, disables reveal and flow, and keeps the static routes and step controls.
Playback speed multiplies visual timing only (including the autoplay interval) and is labelled
`模擬播放速度，非實際鼠類移動速度`.

## D7: Measurement harness

A Playwright script drives the real Next.js app, real API, published aggregate snapshot, and pinned
OSM network with only the external basemap style stubbed. It measures rAF frame deltas and long
tasks during a scripted drag, MapView commit/source/layer/setData counters exposed as
`data-map-perf`, preview latency and payload bytes, reveal frames, playback rebuild deltas, aggregate
request counts, and post-GC JS heap through CDP. The baseline is the HEAD implementation with the
same counters patched in temporarily; both runs use the same viewport, seed, snapshot, and network.

## D8: Tradeoffs and limits

The preview payload is unchanged and still large (about 1.9 MB for the sampled real cell), so the
request remains backend-dominated; this change does not alter serialization. Panning was already
frame-locked on the measurement machine, so the measured win is rebuild elimination, not pan FPS.
Low-end hardware, Safari, and Firefox are not measured. The walker marker uses map coordinates and
line progress, so it inherits MapLibre line rendering limits rather than a custom WebGL layer.
