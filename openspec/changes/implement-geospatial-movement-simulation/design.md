# Design

## Chosen slice

Implement origin transparency/selection and client-side step playback. Do not add per-step aggregate payloads or time semantics.

## API

- Add optional `origin_node_id` request field, validated against loaded graph.
- Default remains deterministic current origin only for compatibility, but response echoes origin.
- Add `step_index` to trajectory steps.
- Preserve bounded trajectory cap and all existing provenance/classification fields.

## Frontend

Workflow: select area → select eligible graph node → configure → run → explore steps.

- Map node selection uses actual returned node IDs, not arbitrary coordinate snapping.
- Selected origin displays node ID/coordinates and `SIMULATED` fixed-origin wording.
- Playback derives slices from completed trajectories locally.
- Controls: previous step, next step, play/pause, reset, current `step k / N`, trajectory selector.
- No elapsed time, speed, moving animal marker, or interpolation claim.
- Dead-end termination shown as graph termination reason; no false arrival.
- Aggregate mode remains cumulative end-state output; trajectory playback is separate.

## Scientific boundaries

Origin is a synthetic model input, not nest/release/animal evidence. Zero visits mean unvisited under origin/seed/steps, not zero rodents. Network is bounded reference/source geometry; no stormwater traversal or biological inference.
