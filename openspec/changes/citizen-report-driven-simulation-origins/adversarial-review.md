# Adversarial review

## Decision

**BLOCKED — full change acceptance remains blocked. Owner-directed bounded real aggregate-origin execution is enabled; approvals and independent review are absent.**

This status reconciles the review after synthetic-only follow-through; it is not an independent re-review. The full change is not Ready for Human Review.

### Addendum 2026-10-27

The project owner directed a bounded activation of real aggregate-cell origins. This is a recorded override, not approval. CR-ORIGIN-001 is narrowed to the missing source/scientific approval, and CR-ORIGIN-003 now reflects an implemented deterministic in-cell resolver (strict for one candidate, uniform for multiple) with an unapproved CRS/coverage/ambiguity policy. CR-ORIGIN-002 and CR-ORIGIN-004 remain unchanged. Full acceptance stays BLOCKED.

## Findings

- **CR-ORIGIN-001 — BLOCKING / OPEN:** a recorded project-owner override now authorizes bounded real aggregate-cell origin execution, but no source, privacy, or scientific approval authorizes approved use.
- **CR-ORIGIN-002 — BLOCKING / OPEN:** Rat Radar reuse remains `UNVERIFIED`; owner assertion is not license, privacy, retention, or derived-use authorization.
- **CR-ORIGIN-003 — BLOCKING / OPEN:** deterministic in-cell resolution is implemented and tested, but approved CRS, coverage, and ambiguity rules are still absent. One candidate is strict; multiple candidates seed walkers uniformly under an owner-directed rule. That rule is not approved science, and centroid or nearest-node snapping would fabricate precision.
- **CR-ORIGIN-004 — BLOCKING / OPEN:** report category, count, month, and cell-selection semantics still require public-health/modeler approval; reports do not establish animal origins or species.
- **CR-ORIGIN-005 — MAJOR / RESOLVED:** current synthetic/node workflow remains available; this slice does not remove or replace it.

## Bounded owner-directed work now enabled

This section supersedes the earlier synthetic-only boundary for explicitly selected OSM aggregate cells.

- `origin_cell_id` is enabled for explicitly selected published aggregate cells on `taipei_osm_songshan`; the synthetic fixture remains a separate path.
- UI labels cell selection separately from resolved node and clears selection when refreshed aggregate data no longer contains the same cell/month/type.
- The resolver rejects zero or boundary candidates without snapping; no centroid or nearest-node fallback. Multiple strictly in-cell candidates are all eligible and seed walkers uniformly with the seeded RNG; whether this is the approved ambiguity rule remains open under CR-ORIGIN-003.
- Responses expose the representative `node_id`, full `node_ids`, candidate count, resolver version, and union reachability; the representative node is the first sorted node, not an observed origin.
- Aggregate data remains `CITIZEN_REPORT_AGGREGATE / UNVERIFIED`; counts never become walkers or weights, and no observed animal movement, species, or risk claim is made.

Written source terms, scientific/CRS approvals, an approved real API/browser workflow, and independent signoffs remain required before final acceptance. Targeted tests do not close these gates.