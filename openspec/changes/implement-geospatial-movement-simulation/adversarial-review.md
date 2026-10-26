# Adversarial review

## Findings before implementation

- AR-001 (BLOCKING): origin is currently insertion-order dependent and invisible. Resolve with optional validated graph-node origin, explicit default disclosure, and response provenance.
- AR-002 (BLOCKING): steps must not become elapsed time, speed, migration, or animal animation. Resolve with step-only labels and client-side slicing of returned edges.
- AR-003 (MAJOR): playback over truncated trajectories can imply all walkers are shown. Resolve with visible `first N of M` copy.
- AR-004 (MAJOR): map click can conflict with layer selection and has no keyboard equivalent. Resolve with node list fallback, click-vs-drag threshold, and accessible names.
- AR-005 (MAJOR): zero visits/disconnected areas can be misread as absence. Resolve with reachability/termination wording and no biological claims.
- AR-006 (MAJOR): source hash evidence is inconsistent in earlier network verification. Reconcile before source acceptance; do not silently rewrite historical evidence.

## Decisions

- Origin: graph node ID only for first slice; no unsupported coordinate snapping. Empty/invalid selection refuses with actionable copy.
- Playback: client-side over completed trajectories; no streaming or per-step aggregate endpoint.
- Default origin: optional for compatibility, but always echoed and visibly labeled as fixed synthetic origin when not user-selected.

Impeccable buildPath remained unavailable in prior redesign work; this change uses repository source review, team feedback, and targeted browser/test evidence rather than inventing a design-system path.
