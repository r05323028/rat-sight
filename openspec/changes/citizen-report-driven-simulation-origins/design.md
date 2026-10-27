# Design

## Existing contract

The aggregate layer remains a privacy-preserving 250 m × month × report-type artifact with suppression and `CITIZEN_REPORT_AGGREGATE / UNVERIFIED`. Owner attestation permits engineering preparation and attribution; it does not prove written publisher terms or approve biological interpretation.

## Resolver

The additive request accepts `origin_cell_id` only with an explicit study area. A pure resolver validates stable cell identity and returns graph nodes only when their coordinates are strictly inside the supplied cell polygon. No centroid, boundary inclusion, or distant nearest-node snapping. Synthetic fixtures and, since 2026-10-27, explicitly selected published aggregate cells on `taipei_osm_songshan` exercise the resolver. Cell counts never become walker counts or transition weights.

A single strictly in-cell candidate is a strict origin (`strict-in-cell-v1`). When more than one candidate is strictly in-cell, every candidate is eligible and each walker starts uniformly from that set with the seeded RNG (`uniform-in-cell-v1`); the representative response node is the first sorted candidate. Zero candidates fail closed. The uniform rule is deterministic but its scientific/ambiguity approval remains open. Resolver provenance retains dataset/version/cell/month/type, source CRS, resolver version, candidate count, representative node ID, full candidate list, and `UNVERIFIED` classification. The simulation engine consumes only resolved internal node IDs and keeps cell identity separate.

## Owner-directed activation (2026-10-27)

The project owner directed the dashboard and API to accept one explicitly selected published aggregate cell as a simulation origin while source-reuse, privacy, and scientific approvals remain open. This is a recorded override, not approval: `AUTHORIZATION=ASSERTED_BY_PROJECT_OWNER`, `REUSE=UNVERIFIED`. The dashboard exposes the cell choice only for `taipei_osm_songshan`, lists only currently published suppressed cells, and sends `origin_cell_id` without `origin_node_id`. The resolver fails closed on zero in-cell nodes; one candidate is strict, and multiple candidates seed walkers uniformly with the seeded RNG (2026-10-27 refinement). The cell used to validate activation, `g250m:11143:49036:2026-05:sighting`, had 83 eligible nodes in the then-pinned snapshot, so a one-node-only rule would have made the activation unusable; the owner chose uniform seeding explicitly. The current snapshot covers all 91 published cells with 3–286 eligible nodes each. Responses retain `cell_candidate_count`, `cell_resolver_version`, the representative `node_id`, and the full `node_ids`; UI copy keeps the cell `UNVERIFIED` and the movement `SIMULATED`; it does not claim legal reuse or biological meaning. Clicking a map marker focuses it and opens a detail card; focus alone neither populates the origin nor runs a simulation. The card's explicit run action, or the advanced cell control, chooses the cell as origin. CRS/coverage/ambiguity approval remains an open blocker (CR-ORIGIN-003), so this is an engineering rule, not approved science.

## Coverage and local map subset (2026-10-27)

The pinned OSM snapshot was expanded from a 0.004° Songshan extract to 30 clustered 500 m-buffered neighborhoods around all 91 currently published aggregate cells. It has 71,281 graph nodes and 185,503 edges, and a 91-cell probe resolved every cell with 3–286 strictly in-cell candidates. The immutable parse is cached by path, pinned SHA-256, and modification time, and callers treat the graph as read-only.

Simulation and reachability stay on the full graph. A 26 MB graph is unsuitable for every interactive map response, so the API may return a `local_reference` subset containing all origin nodes, trajectory-touched nodes, nodes within 750 m of the representative origin, and their connecting edges. `visualization` reports the mode, radius, returned and full counts, and a note; the dashboard uses full-graph reachability totals and labels the local subset. Synthetic graphs remain unfiltered. Coverage is still an engineering artifact, not an approved CRS/coverage policy (CR-ORIGIN-003).

## Synthetic fixture preview input

The dashboard may offer an explicit `synthetic-cell-n0` origin control only for `taipei_synthetic_demo`. This input is a bounded test fixture, not a Rat Radar cell or a proxy for any report. Focusing a citizen-report aggregate marker exposes aggregate details in a card but MUST NOT populate the simulation request by itself; an explicit card action or the separate advanced aggregate-cell control is described above. Selecting a fixture origin sends `origin_cell_id` without `origin_node_id`; changing study area clears it, and the control is unavailable for OSM.

## UI boundary

Published aggregate cells render as representative red markers for display and selection, not as exact report locations. Technical graph-node markers remain hidden from the primary dashboard. Clicking a marker highlights it and opens a detail card with aggregate count, month, type, centroid caveat, `UNVERIFIED` classification, and attribution; focus alone does not send a simulation request. The card's explicit run action or a separate advanced control lists the currently published aggregate cell as an origin. The existing synthetic/node development workflow remains isolated. Attribution is always visible: 資料來源：見鼠雷達 Rat Radar — https://ratdar.taipei/.
