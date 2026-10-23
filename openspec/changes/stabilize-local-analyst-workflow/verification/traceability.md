# Traceability

| Requirement | Implementation | Evidence | Status |
|---|---|---|---|
| R1 isolated loopback runtime | `apps/web/next.config.ts`, proposal/design launch instructions | `make geospatial-smoke` + `make rodent-report-smoke` at 127.0.0.1:3010; `qa.md` | VERIFIED |
| R2 Asia/Taipei inclusive filtering | `apps/web/src/lib/api.ts`, `apps/web/src/components/dashboard.tsx` | `api.test.ts`, `dashboard.test.tsx`, `qa.md` | VERIFIED |
| R3 honest layer rows/counts | `apps/web/src/components/dashboard.tsx`, `globals.css` | `dashboard.test.tsx`, `qa.md` | VERIFIED |
| R4 returned/truncated report semantics | `apps/web/src/components/dashboard.tsx` | `dashboard.test.tsx`, updated `real-rodent-report.spec.ts` | VERIFIED |

Scientific status remains unchanged: fixtures are `SIMULATED`; no observed counts, risk, movement, prevalence, hotspot, completeness, or intervention claim is introduced.
