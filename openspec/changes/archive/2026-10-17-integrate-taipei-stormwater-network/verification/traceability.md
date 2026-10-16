# Traceability Validation

Evidence ID: `EVID-TPE-STORMWATER-NETWORK-2026-10-16`

| Requirement | Implementation | Tests / verification | Status |
|---|---|---|---|
| `stormwater-network#verified-stormwater-source-import` | `services/api/src/ratsight_api/importers/stormwater_pipelines.py`; `services/api/src/ratsight_api/domain/stormwater.py`; `Makefile` | `services/api/tests/test_stormwater_pipelines_import.py`; importer and smoke runs recorded in `verification/qa.md` | VERIFIED |
| `stormwater-network#idempotent-stormwater-persistence` | `services/api/src/ratsight_api/importers/stormwater_pipelines.py`; `services/api/src/ratsight_api/infrastructure/database/models.py`; `services/api/alembic/versions/0003_stormwater_pipelines.py` | `services/api/tests/test_stormwater_pipelines_import.py`; backend suite; QA smoke | VERIFIED |
| `stormwater-network#stormwater-geojson-api` | `services/api/src/ratsight_api/api/routes/stormwater_pipelines.py`; `services/api/src/ratsight_api/application/stormwater_pipelines.py`; `services/api/src/ratsight_api/api/schemas.py` | `services/api/tests/test_api.py`; `scripts/geospatial_smoke.sh`; QA evidence | VERIFIED |
| `stormwater-network#stormwater-dashboard-inspection` | `apps/web/src/components/dashboard.tsx`; `apps/web/src/components/map-view.tsx`; `apps/web/src/lib/api.ts` | `apps/web/src/components/dashboard.test.tsx`; `apps/web/src/components/map-view.test.tsx`; `apps/web/e2e/real-stormwater.spec.ts`; `apps/web/e2e/real-stormwater-empty.spec.ts`; QA evidence | VERIFIED |
| `stormwater-network#existing-layer-integrity` | `packages/simulation`; `apps/web/src/components/map-view.tsx`; `scripts/verify_official_districts.sh` | simulation regression tests; `apps/web/e2e/official-district.spec.ts`; one-time official verification; QA evidence | VERIFIED |

## Classification and limitations

The stormwater layer is `INFRASTRUCTURE_REFERENCE` and `UNVERIFIED`; it is not an observation, simulation, inferred connectivity graph, traversability claim, or risk estimate. Synthetic fixtures remain `SIMULATED`. The selected Candidate B source was verified by metadata and hash, but the full official stormwater XML has not been imported in this change; deterministic local importer and isolated synthetic smoke are verified. No scientific claim or model validation applies (`science.applicable=false`).
