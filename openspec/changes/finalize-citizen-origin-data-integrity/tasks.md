# Tasks

## Specification and design

- [x] 1. Review the inherited origin contract, snapshot provenance fields, importer suppression rules, dashboard selection state, and the pinned network loader.
- [x] 2. Write the delta requirements for snapshot binding, fail-closed resolution, category eligibility, provenance, refresh integrity, coverage diagnostics, and measured performance.

## Implementation

- [x] 3. Require `origin_source` (dataset id, resource version, content SHA-256) for OSM cell origins and reject it for the synthetic demo branch in `services/api/src/ratsight_api/api/schemas.py`.
- [x] 4. Read the published version and digest together and resolve the cell in one pinned row query in `services/api/src/ratsight_api/application/citizen_report_aggregates.py`; drop the unpinned cell-polygon helper.
- [x] 5. Map a stale version or digest to `409 ORIGIN_SOURCE_VERSION_CONFLICT`, an unknown dataset to `422 ORIGIN_SOURCE_UNKNOWN`, and ineligible categories to `422 ORIGIN_REPORT_TYPE_INELIGIBLE` in `services/api/src/ratsight_api/api/routes/simulations.py`.
- [x] 6. Make a suppressed cell indistinguishable from an absent one and evaluate category eligibility only after publication, suppression, and classification checks pass.
- [x] 7. Centralize the eligibility policy (`origin_eligibility`, `ORIGIN_POLICY_VERSION`) in `services/api/src/ratsight_api/domain/citizen_report_aggregates.py` and expose it through the aggregate feature properties.
- [x] 8. Record the snapshot actually used (dataset, version, digest, category, eligibility, policy version, resolution method, resolver version, candidate count) in the preview response, separate from OSM provenance.
- [x] 9. Bind dashboard selection to its source snapshot, invalidate on a real source change only, tag previews with their snapshot, and surface the refresh notice and ineligible-marker explanation in Traditional Chinese.
- [x] 10. Add `scripts/citizen_origin_coverage.py` for repeatable published-cell coverage and drift diagnostics with no expected-count constant.
- [x] 11. Add `scripts/benchmark_simulation.py` and reduce measured reachability cost with one multi-source traversal plus per-graph component memoization, without changing the response contract.

## Verification

- [x] 12. Cover snapshot identity, stale version, stale digest, removed cell, suppressed cell, unknown dataset, category eligibility, provenance, and determinism in API, service, and dashboard tests.
- [x] 13. Run the full repository checks (`make test-py`, `make test-js`, `make typecheck`, `make lint`, `make format-check`, `make build`) and `bash scripts/geospatial_smoke.sh`.
- [x] 14. Run the coverage diagnostic against the published snapshot and record the benchmark report under `docs/benchmarks/`.
- [x] 15. Run the real published-snapshot browser workflow on desktop and mobile. Executed 2026-10-27 against the read-only published aggregate, real API, and pinned OSM network: 2/2 passed (desktop 7.5 s, mobile 7.4 s) with the exact `origin_source` in the request and full provenance in the response; recorded in `verification/qa.md` (FCO-006). The temporary spec was removed, so the committed smoke remains fixture-only.
- [ ] 16. Obtain public-health/modeler approval of the eligibility policy and cell-to-origin semantics. **BLOCKED:** human decision (FCO-001, CR-ORIGIN-004).
- [ ] 17. Obtain source-authorization, privacy, and independent-review evidence. **BLOCKED:** inherited from `citizen-report-driven-simulation-origins` (CR-ORIGIN-001..003); not owned by this change.
- [ ] 18. Run the quality gate and stop Ready for Human Review. **BLOCKED** by task 16 and the approval record.

Status: all engineering tasks are complete, including real-snapshot browser verification. This change is not Ready for Human Review: the eligibility policy still requires a human scientific decision (task 16), task 17 inherits unresolved source/privacy/independent-review items, and task 18 blocks until then.
