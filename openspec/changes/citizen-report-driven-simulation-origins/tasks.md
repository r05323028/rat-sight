# Tasks

## Evidence and approval

- [x] 1. Inspect aggregate source, suppression, API, map, simulation, and active P0 contracts.
- [x] 2. Obtain public-health, modeler, infrastructure, reviewer, and QA assessments.
- [ ] 3. Obtain source-owner/legal/privacy approval for derived aggregate use.
- [ ] 4. Obtain public-health/modeler approval for report category and cell-to-origin semantics.
- [ ] 5. Approve CRS, coverage, candidate matching, ambiguity, and no-candidate rules. The current owner-directed engineering rule resolves every strictly in-cell candidate (one strict, multiple uniform); the CRS/coverage/ambiguity policy itself remains unapproved.

## Implementation after approval

- [x] 6. Add additive `origin_cell_id` contract and provenance; retain legacy node mode only as isolated development/test mode for synthetic fixtures.
- [x] 7. Add deterministic in-cell candidate resolver; zero candidates fail closed, one candidate is strict, and multiple candidates return all eligible nodes for uniform seeding without snapping.
- [x] 8. Replace aggregate grid rendering with representative red markers, click focus, and highlight selection; retain separate development node workflow.
- [x] 9. Complete synthetic-only cell/node display distinction, stale selected-cell clearing, playback, and disclosures. A separate OSM aggregate-cell control and disclosure were added on 2026-10-27.

## Implementation after approval

- [ ] 10. Close real aggregate-cell approval and acceptance. Execution is enabled under the 2026-10-27 project-owner override, but tasks 3–5 remain open and this task stays incomplete until they are recorded and reviewed.

## Verification

- [ ] 11. Complete remaining privacy/suppression, invalid/stale, CRS, deterministic-resolution, and compatibility tests. Synthetic no-candidate, multi-candidate, unknown-cell-ID, mutually-exclusive-origin, malformed-polygon, strict-boundary, deterministic-resolution, explicit EPSG:4326 metadata, stale-selection, and aggregate suppression/API contract tests exist. Real-cell tests cover one isolated OSM node polygon and a multi-node cell that seeds all candidates uniformly; broader CRS/coverage/ambiguity and approved real-data workflow tests remain open.
- [ ] 12. Run real approved API/browser workflow desktop/mobile.
- [ ] 13. Obtain independent reviewer, QA, public-health, modeler, and municipal-analyst evidence.
- [ ] 14. Run final quality gate and stop Ready for Human Review; do not archive without owner acceptance.
- [x] 15. Add an explicit synthetic-fixture origin control and preview request path; keep aggregate marker selection independent and disable the control outside the synthetic demo area.

- [x] 16. Record the 2026-10-27 project-owner override and ship explicit OSM aggregate-cell origin selection with deterministic in-cell resolution (strict for one candidate, uniform for multiple), candidate-count/resolver/node-list provenance, fail-closed zero-candidate errors, the expanded pinned OSM snapshot, and counts-never-weights disclosure; approvals remain open.
- [x] 17. Add a focused aggregate-cell detail card: marker click highlights and opens aggregate-only details without setting an origin or running; the card's explicit action runs that cell and sends `origin_cell_id` without `origin_node_id`.
- [x] 18. Expand the pinned OSM network to cover all 91 currently published aggregate cells (all resolve with at least one in-cell node), cache immutable graph parsing, and return a disclosed 750 m `local_reference` map subset while simulation and reachability use the full graph.

Status: 10/18 tasks complete. Owner-directed real aggregate-cell origins are implemented with uniform seeding across all strictly in-cell nodes and targeted tests pass; approval tasks 3–5, an approved real-data workflow, independent review, and full acceptance remain BLOCKED. Not Ready for Human Review. Redistribution and biological interpretation require written source terms and explicit scientific/CRS approval.
