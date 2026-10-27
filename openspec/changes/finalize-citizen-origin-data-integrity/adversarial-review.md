# Adversarial review

## Decision

**BLOCKED — engineering findings are resolved, one approval-dependent finding remains open.**

The origins, eligibility, provenance, coverage, performance, and real-snapshot browser verification work is implemented and covered by tests. The change cannot be accepted while the report-category eligibility policy and cell-to-origin semantics lack public-health and modeler approval; that decision belongs to a human and is not replaced by this review.

## Findings

- **FCO-001 — BLOCKING / OPEN:** the eligibility policy (sighting eligible; bait-station and other context-only) is a new scientific assumption about what constitutes candidate-origin evidence. It is recorded, versioned, and enforceable, but it is not approved science. Carried over from CR-ORIGIN-004 in `citizen-report-driven-simulation-origins`.
- **FCO-002 — MAJOR / RESOLVED:** a cell identity resolved against the latest import created a time-of-check/time-of-use window. Resolved by a single published version+digest check followed by one pinned row query; stale version or digest now returns 409.
- **FCO-003 — MAJOR / RESOLVED:** suppression failures produced a distinct error from absent cells, which confirmed the existence of a suppressed cell. Resolved by raising the same not-found error for both, with a test asserting the messages are identical.
- **FCO-004 — MAJOR / RESOLVED:** reachability repeated a full BFS per candidate node and materialized a 50k-node subgraph, dominating preview latency. Resolved by one multi-source traversal plus membership edge counting; equivalence tests pin the result.
- **FCO-005 — MINOR / OPEN:** preview payloads reach ~1.8 MB at 500 walkers/50 steps. Recorded as a capacity limitation; no payload redesign was attempted in this change.
- **FCO-006 — MAJOR / RESOLVED:** real-snapshot browser verification ran against the read-only published aggregate, real API, and pinned network: 2/2 passed (desktop 7.5 s, mobile 7.4 s), asserting the exact `origin_source`, the response provenance, the marker/card content, and playback. The temporary spec was deleted afterwards so only the fixture smoke is committed; the procedure is recorded in `verification/qa.md`.

## Tested boundary

- Version or digest drift cannot silently resolve: service tests and route tests cover 409, unknown dataset, removed cell, suppressed cell, and stored-provenance mismatch.
- Category rejection is enforced server-side: route tests post bait and unknown categories and receive 422 with the policy reason and `UNVERIFIED` classification.
- Synthetic fixtures remain isolated behind their own dataset prefix, flag, and provenance model.
- The reachability optimization is verified against `nx.descendants` unions and `subgraph().number_of_edges()` on a graph with parallel edges.

## Not verified here

- Scientific validity of sighting-only eligibility, of a 250 m cell as a candidate origin, or of uniform graph-node seeding.
- Source reuse authorization, written publisher terms, privacy review, and independent review.
- Absolute performance on other hardware; measurements describe the recorded machine and network snapshot only.
