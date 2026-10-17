# Traceability Validation

| Requirement | Implementation | Tests / verification | Status |
|---|---|---|---|
| `rodent-report-stabilization#Immutable smoke reset` | `scripts/seed_rodent_report_smoke.py`; `scripts/rodent_report_smoke.sh`; `services/api/alembic/versions/0006_rodent_reports_immutability.py` | `scripts/tests/test_seed_rodent_report_smoke.py`; `make rodent-report-smoke`; QA | VERIFIED |
| `rodent-report-stabilization#Consistent simulated classification` | `services/api/alembic/versions/0005_rodent_reports_simulated.py`; `services/api/src/ratsight_api/infrastructure/database/models.py`; `services/api/src/ratsight_api/application/rodent_reports.py` | backend classification/route tests; full pytest; QA | VERIFIED |
| `rodent-report-stabilization#Bounded report inspection` | `apps/web/src/components/dashboard.tsx`; `apps/web/src/components/map-view.tsx` | frontend unit tests; live rodent smoke; QA | VERIFIED |
| `rodent-report-stabilization#Temporal validation and map interaction` | `apps/web/src/components/dashboard.tsx`; `apps/web/src/lib/api.ts`; `apps/web/e2e/real-rodent-report.spec.ts` | dashboard tests; live rodent smoke; default E2E; QA | VERIFIED |

## Integrity

Rodent reports remain fixture-only `RODENT_REPORT` / `SIMULATED`; no external citizen data was accessed. Administrative, stormwater, and simulation layers remain independent. Smoke resources were isolated and cleaned; shared development PostGIS was untouched.
