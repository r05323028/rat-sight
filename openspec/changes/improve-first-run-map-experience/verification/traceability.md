# Traceability Validation

| Requirement | Implementation | Verification | Status |
|---|---|---|---|
| first-run-map#First-run data status | `apps/web/src/components/dashboard.tsx` | `dashboard.test.tsx` unavailable/viewport/error coverage; typecheck/lint/build; post-fix browser pass on the isolated instance | VERIFIED (UI contract); live browser VERIFIED on synthetic fixture data only — authoritative-data path untested |
| first-run-map#Layer catalog clarity | `apps/web/src/components/dashboard.tsx` | `dashboard.test.tsx` grouping and simulated-path transition | VERIFIED |
| first-run-map#Synthetic preview interpretation | `apps/web/src/components/dashboard.tsx` | `dashboard.test.tsx` pre/post-run copy and metrics | VERIFIED |
| first-run-map#Understandable report filtering | `apps/web/src/components/dashboard.tsx`, `apps/web/e2e/real-rodent-report.spec.ts` | focused tests and query-contract assertion; post-fix browser pass issued bounded `rodent-reports` bbox queries | VERIFIED; runtime queries observed in browser — filtering semantics covered by tests |

No API contract, dataset, importer, authentication, or scientific model changed. The post-fix browser acceptance ran on an isolated instance (byte-identical sources at `http://127.0.0.1:3002`, live API `http://127.0.0.1:8000`) because the long-running `:3000` dev instance serves the post-fix markup without hydrating for a fresh browser; that limitation is preserved in `verification/qa.md`.
