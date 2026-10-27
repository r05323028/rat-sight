# Design

## Chosen slice

Implement origin transparency/selection and client-side step playback. Do not add per-step aggregate payloads or time semantics.

## API

- Require an explicit origin. The public OSM analyst contract accepts an eligible `origin_cell_id`; the isolated synthetic demo accepts an explicit graph-node or fixture-cell origin. Missing, mixed, invalid, and arbitrary default origins are rejected. (Corrected 2026-10-27 after the earlier compatibility default was removed.)
- Response echoes origin classification, identity, coordinates, and synthetic/non-observational meaning.
- Add `step_index` to trajectory steps.
- Preserve bounded trajectory cap and all existing provenance/classification fields.

## Frontend

Workflow: select area → select eligible aggregate cell (public OSM) or explicit fixture origin (synthetic demo) → configure → run → explore steps.

- Map node selection uses actual returned node IDs, not arbitrary coordinate snapping.
- The public analyst UI does not expose arbitrary graph-node selection.
- Selected origin displays node ID/coordinates and `SIMULATED` fixed-origin wording.
- Playback derives slices from completed trajectories locally.
- Controls: previous step, next step, play/pause, reset, current `step k / N`, trajectory selector.
- No elapsed time, speed, moving animal marker, or interpolation claim.
- Dead-end termination shown as graph termination reason; no false arrival.
- Aggregate mode remains cumulative end-state output; trajectory playback is separate.

## Scientific boundaries

Origin is a synthetic model input, not nest/release/animal evidence. Zero visits mean unvisited under origin/seed/steps, not zero rodents. Network is bounded reference/source geometry; no stormwater traversal or biological inference.

OSM `oneway` is vehicle metadata, not evidence of rat movement direction. The baseline graph adds bidirectional movement edges over shared-node topology, preserves the original tag, and reverses geometry on the reverse edge. This is a hypothetical uncalibrated baseline, not a biological claim.
