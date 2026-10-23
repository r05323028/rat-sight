# Code review

**Decision: PASS.**

Reviewed current source, connected tests, runtime config, README, and API contracts. Taipei conversion uses explicit UTC arithmetic and preserves RFC3339 output; equal bounds remain valid. Layer count matches rendered rows, unavailable catalog entries have status text rather than dead checkboxes, and truncated responses explicitly avoid claiming totals. No backend contract, database, scientific classification, or shared runtime ownership changed.

### LAW-CR-003 — MEDIUM — RESOLVED

`README.md:38-52` now gives executable `make geospatial-smoke` and `make rodent-report-smoke` paths. The checked-in harnesses perform free-port checks, create project-scoped disposable Compose volumes, run migrations and synthetic fixtures, launch API/Web with explicit ports and API URL, check `/health`, execute Playwright browser checks, and clean up their own resources. Manual launch flags and ownership boundaries are also documented.

Fresh-browser hydration/API interaction passed through both isolated harnesses: geospatial smoke and rodent-report smoke. Synthetic fixture data only; no authoritative data claim.

### LAW-CR-004 — MAJOR — RESOLVED

The broad listener sweep was removed from `scripts/geospatial_smoke.sh`; both smoke harnesses now clean up only recorded API/Web child trees and their owned Compose project/volume. Port checks remain fail-closed before startup. The unrelated-process termination finding is resolved.

### Verification limitation

Municipal browser QA passed on the isolated runtime: four checkboxes correspond to the four built-in available layers; unavailable catalog entries remain status-only. No authoritative data workflow or real-world counts were tested; synthetic fixtures remain visibly synthetic. Shared `localhost:3000` was not restarted or mutated.

Automated focused tests rerun during review: `corepack pnpm --filter @ratsight/web test -- --run src/components/dashboard.test.tsx src/lib/api.test.ts` — PASS, 3 files / 57 tests. Both smoke harnesses passed fresh-browser hydration/API checks. `bash -n scripts/geospatial_smoke.sh scripts/rodent_report_smoke.sh` and `git diff --check` — PASS.
