# Tasks

## 1. Specification and design
- [x] 1.1 Record proposal, design, and the `web-localization` delta (zh-Hant copy, token glosses, verbatim machine values, zh-Hant metadata).
- [x] 1.2 Confirm scope with the owner: zh-TW only, no language switcher, status tokens keep their canonical English form plus a Chinese gloss.

## 2. Interface localization
- [x] 2.1 Translate dashboard copy (headings, controls, loading/empty/error states, help notes, accessible names) in `apps/web/src/components/dashboard.tsx`.
- [x] 2.2 Translate the map surface and document metadata (`apps/web/src/components/map-view.tsx`, `apps/web/src/app/layout.tsx`).
- [x] 2.3 Own catalog display copy in the UI: `LAYER_LABEL_OVERRIDES`, `LAYER_UNAVAILABLE_MESSAGES`, `CLASSIFICATION_LABELS`, and a neutral `未命名資料圖層` fallback so API English never renders.
- [x] 2.4 Keep canonical tokens (`OBSERVED`, `INFERRED`, `SIMULATED`, `UNVERIFIED`, `RODENT_REPORT`, provenance ids) and machine values (UTC timestamps, ids, seeds, counts) verbatim.

## 3. Tests
- [x] 3.1 Update unit tests for translated copy, token glosses, and the unknown-layer fallback (58 tests across 3 files).
- [x] 3.2 Update Playwright specs for the zh-Hant accessible names and selectors (dashboard 5/5).

## 4. Evidence and review
- [x] 4.1 Run unit, typecheck, lint, build, and dashboard e2e; record commands and results in `verification/qa.md`.
- [x] 4.2 Run an adversarial review; record AR-L10N-001 (MAJOR, resolved) and AR-L10N-002 (MEDIUM, resolved) in `verification/adversarial-review.md`.
- [x] 4.3 Record requirement-to-evidence mapping in `verification/traceability.md` and the gate record in `verification/gate.json`.
- [x] 4.4 Complete an independent code review of the localized implementation.
