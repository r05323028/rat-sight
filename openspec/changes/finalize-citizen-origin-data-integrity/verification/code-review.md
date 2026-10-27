# Code review

## Decision

**PASS_WITH_WARNINGS** — no unresolved correctness defect found in the changed code; one recorded capacity limit (payload size) and one inherited, non-code approval block remain.

## Scope

Backend: `services/api/src/ratsight_api/{api/schemas.py,api/routes/simulations.py,application/citizen_report_aggregates.py,application/simulation_preview.py,domain/citizen_report_aggregates.py}`. Frontend: `apps/web/src/{lib/api.ts,components/dashboard.tsx,app/globals.css}` plus tests. Simulation: `packages/simulation/src/ratsight_simulation/graph/network.py`. Tooling: `scripts/{citizen_origin_coverage.py,benchmark_simulation.py,openspec_quality_gate.py}` and `scripts/tests/test_citizen_origin_coverage.py`.

## Findings

- **Snapshot resolution (FCO-002): resolved.** Version and digest are read together, then the cell row is fetched by dataset + version + digest + identity in one query. A stale version or digest is a 409 before any cell lookup, so a removed cell cannot be misreported as a version conflict or vice versa.
- **Suppression (FCO-003): resolved.** A suppressed row raises the same error text as an absent row; the test asserts string equality. No branch reveals suppressed existence.
- **Eligibility (FCO-001): policy implemented, approval outstanding.** One function in the domain layer decides eligibility; routes and UI consume it. Rejection happens after publication, suppression, and classification checks.
- **Reachability (FCO-004): resolved.** One multi-source BFS and membership edge counting replace per-origin `nx.descendants` and `subgraph().number_of_edges()`; results are pinned by an equivalence test with parallel edges. The component count is memoized per graph object, which is safe because the loader returns a fresh graph when the pinned source changes.
- **Payload (FCO-005): open, minor.** 1.77 MB at 500 walkers/50 steps. Recorded as a capacity limitation; no redesign attempted.
- **Real-snapshot browser verification (FCO-006): resolved.** Executed desktop and mobile against the published snapshot and pinned network; see `verification/qa.md` and `adversarial-review.md`.

## Residual risk

- Policy validity and cell semantics remain a scientific/human decision, tracked as FCO-001.
- Measurements are machine-specific.
- The temporary real-snapshot spec is not part of the committed suite; regression protection for that exact path relies on the fixture smoke plus the new API/service tests.
