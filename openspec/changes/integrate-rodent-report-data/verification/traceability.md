# Traceability Validation

Evidence: `docs/evidence/rodent-report-source-investigation-2026-10-17.md` (candidate investigation only; no real records used).

| Requirement | Implementation | Tests / evidence | Status |
|---|---|---|---|
| `rodent-reports#Rodent report source boundary` | `proposal.md`; `design.md`; `services/api/tests/fixtures/rodent_reports/README.md` | source investigation; importer pinning tests; QA smoke | VERIFIED (fixture-only; real source blocked) |
| `rodent-reports#Validated rodent report import` | `services/api/alembic/versions/0004_rodent_reports.py`; `services/api/src/ratsight_api/importers/rodent_reports.py`; `services/api/src/ratsight_api/api/schemas.py` | `services/api/tests/test_rodent_reports_import.py`; QA smoke | VERIFIED |
| `rodent-reports#Bounded rodent report API` | `services/api/src/ratsight_api/application/rodent_reports.py`; `services/api/src/ratsight_api/api/routes/rodent_reports.py`; `services/api/src/ratsight_api/api/schemas.py` | `services/api/tests/test_rodent_reports_api.py`; QA smoke | VERIFIED |
| `rodent-reports#Rodent report dashboard inspection` | `apps/web/src/components/dashboard.tsx`; `apps/web/src/components/map-view.tsx`; `apps/web/src/lib/api.ts` | frontend unit tests; `apps/web/e2e/real-rodent-report.spec.ts`; QA smoke | VERIFIED |
| `rodent-reports#Existing layer integrity` | `apps/web/src/components/map-view.tsx`; `apps/web/src/components/dashboard.tsx` | `apps/web/e2e/dashboard.spec.ts`; `make geospatial-smoke` (V13: live administrative/stormwater populated and empty states) | VERIFIED |

## Classification, privacy, and limitations

Synthetic fixture rows are `data_class=RODENT_REPORT`, `classification=SIMULATED`, and are not observations. No real citizen reports, photos, names, addresses, or source payloads were downloaded, stored, or redistributed. `source_record_id` and source coordinates are importer-only; the API exposes only the exact allowlist. Real source authorization, license/reuse, privacy/retention, spatial disclosure, and public-health acceptance remain required before any real integration. No biological, prevalence, causal, movement, risk, disease, or intervention claim is made.
