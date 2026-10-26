# Traceability

| Requirement | Implementation | Tests | Verification |
|---|---|---|---|
| `map-exploration#First-run orientation` | `apps/web/src/components/dashboard.tsx` | `apps/web/src/components/dashboard.test.tsx` | V-TEST, V-E2E |
| `map-exploration#Map-first task flow` | `apps/web/src/components/dashboard.tsx`, `apps/web/src/app/globals.css` | `apps/web/src/components/dashboard.test.tsx` | V-TEST, V-E2E |
| `map-exploration#Honest synthetic demonstration` | `apps/web/src/components/dashboard.tsx` | `apps/web/src/components/dashboard.test.tsx`, `apps/web/e2e/dashboard.spec.ts` | V-TEST, V-E2E, V-REAL |
| `map-exploration#Actionable data states` | `apps/web/src/components/dashboard.tsx` | `apps/web/src/components/dashboard.test.tsx` | V-TEST, V-E2E |
| `map-exploration#Accessible responsive workflows` | `apps/web/src/components/dashboard.tsx`, `apps/web/src/app/globals.css`, `apps/web/playwright.config.ts` | `apps/web/e2e/dashboard.spec.ts` | V-E2E, V-REAL, V-A11Y, V-TYPE, V-LINT |
| `map-exploration#Independent synthetic reports` | `apps/web/src/components/dashboard.tsx` | `apps/web/src/components/dashboard.test.tsx`, `apps/web/e2e/dashboard.spec.ts` | V-TEST, V-E2E, V-REAL |
