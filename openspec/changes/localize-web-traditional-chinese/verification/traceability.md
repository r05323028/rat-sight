# Traceability

| Requirement | Implementation | Tests | Evidence | Status / limits |
| --- | --- | --- | --- | --- |
| `web-localization#Traditional Chinese interface copy` | `apps/web/src/components/dashboard.tsx`, `apps/web/src/components/map-view.tsx`, `apps/web/src/app/layout.tsx` | `apps/web/src/components/dashboard.test.tsx`, `apps/web/src/components/map-view.test.tsx`, `apps/web/e2e/dashboard.spec.ts` | `V-UNIT`, `V-TYPE`, `V-LINT`, `V-BUILD`, `V-E2E`, `V-BROWSER` | VERIFIED — static copy, statuses, errors, and accessible names are zh-Hant; English API prose is intercepted by UI-owned copy. |
| `web-localization#Canonical scientific tokens preserved` | `apps/web/src/components/dashboard.tsx` (`CLASSIFICATION_LABELS`) | `apps/web/src/components/dashboard.test.tsx` | `V-UNIT`, `V-BROWSER` | VERIFIED — tokens render verbatim with a Chinese gloss (e.g. `OBSERVED · 已觀測`, `SIMULATED · 模擬`); unknown layer ids fall back to `未命名資料圖層`. |
| `web-localization#Machine-readable values remain verbatim` | `apps/web/src/components/dashboard.tsx`, `apps/web/src/components/map-view.tsx` | `apps/web/src/components/dashboard.test.tsx`, `apps/web/e2e/real-rodent-report.spec.ts` | `V-UNIT`, `V-E2E`, `V-BROWSER` | VERIFIED — UTC timestamps, ids, seeds, and counts are unchanged; some English provenance strings remain by design. |
| `web-localization#Traditional Chinese document metadata` | `apps/web/src/app/layout.tsx` | e2e document assertions, browser probe | `V-E2E`, `V-BROWSER` | VERIFIED — `lang="zh-Hant"`, zh-Hant title and description observed in the rendered page. |

Verification ids are defined in `verification/gate.json`; runtime limits are recorded in
`verification/qa.md` (synthetic fixture data only, no authoritative dataset).
