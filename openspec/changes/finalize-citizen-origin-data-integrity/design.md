# Design

## Decisions

### D1. Verify version and digest together, then pin the row
`get_citizen_report_origin_cell` reads the published `(resource_version, content_sha256)` pair in one query, rejects a mismatch as `CitizenReportSourceVersionConflict`, and then selects the cell with `dataset_id + resource_version + content_sha256 + cell_id + month + report_type` in a single pinned row query. Geometry, provenance, classification, and count therefore come from one snapshot, and identity is never resolved by `cell_id` alone.

Rejected alternatives: a `latest` flag per row (adds state without fixing TOCTOU); client-supplied geometry (untrusted); a separate version table (new infrastructure for a two-column invariant).

### D2. HTTP 409 for source conflict, 422 for ineligible identity
A stale version or digest means the client's reviewed snapshot is gone, so `409 ORIGIN_SOURCE_VERSION_CONFLICT` carries the requested dataset id, version, and refresh action. Absent cells, unknown datasets, and category rejections stay `422`, so 409 is never used to leak cell state.

### D3. Suppressed cells are indistinguishable from absent ones
A row failing the suppression minimum raises `CitizenReportCellNotFound` with the same message as a genuinely absent cell, because "suppressed" confirms the cell exists in the source snapshot. Category eligibility is evaluated only after publication, suppression, and classification checks pass, so no error path distinguishes them.

### D4. One eligibility policy in the domain layer
`origin_eligibility(report_type)` in `domain/citizen_report_aggregates.py` returns `(eligible, reason)` with `ORIGIN_POLICY_VERSION`; API schemas, routes, importers, and the dashboard consume its payload rather than re-declaring categories. The conservative default (`sighting` only) is a product and modeling policy, not evidence that sightings are verified animal locations, and it remains subject to public-health and modeler approval (CR-ORIGIN-004).

### D5. Provenance is returned, not implied
`PreviewOrigin` carries `source_dataset_id`, `source_resource_version`, `source_content_sha256`, `source_report_type`, `source_report_type_eligible`, `source_origin_policy_version`, and `origin_snapshot_reference` next to the OSM source fields, so a report from an older snapshot can be identified from the payload alone.

### D6. Frontend keywords selection on source identity
The dashboard stores the source identity next to the selected marker and compares it with the current aggregate response. Equality keeps the selection (viewport refetches), inequality clears selection and preview, and each preview response is tagged with the snapshot it used so an older response cannot be displayed against a newer one.

### D7. Coverage diagnostic is a script with a narrow contract
`scripts/citizen_origin_coverage.py` reuses `resolve_origin_cell` and `load_osm_surface_graph`, reports counts and drift, exits 2 when the snapshot or network is unavailable, and exits 0 for any measured coverage — including gaps. It deliberately has no expected-cell-count constant.

### D8. Reachability uses one multi-source traversal
Measurement showed per-origin `nx.descendants` plus `subgraph(...).number_of_edges()` consumed ~3.7 s of a ~4.3 s preview for 25 origins. `reachability_summary` now performs one multi-source BFS and counts reachable edges by membership, with the component count memoized per graph object in a `WeakKeyDictionary` (a new graph object is created whenever the pinned source changes, so stale topology cannot be served).

## Risks and limits

- Category eligibility is a modeling policy pending scientific approval; the engineering test suite proves enforcement, not scientific validity.
- Report cells remain `UNVERIFIED` aggregates; graph-node seeding remains an engineering baseline, not rodent ecology.
- Payloads grow with walkers and steps (measured 0.79–1.77 MB at 24/12, 100/30, 500/50). This is recorded as a capacity limit rather than redesigned in this change.
- Real-snapshot browser verification ran on 2026-10-27 against the read-only published aggregate, real API, and pinned network (desktop + mobile, 2/2 passed); the spec was temporary, so the committed smoke stays fixture-only and is not described as real-data verification.
