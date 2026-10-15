# RatSight Global Agent Contract

## Scientific integrity
- Keep `OBSERVED`, `INFERRED`, `SIMULATED`, and `UNVERIFIED` distinct in storage, API, UI, and documents.
- Never invent scientific evidence, Taipei counts or routes, or biological constants.
- Do not invent causal claims or model-accuracy metrics.
- Never present simulated rodent movement as an observed migration or real-world event.
- Mark unavailable data as unavailable; absence is not a zero count or observation.
- Preserve source, license, CRS, processing, assumptions, model/version/seed, and uncertainty where applicable.

## Architecture boundaries
- Frontend uses Next.js and MapLibre; backend uses FastAPI and PostGIS.
- Geo and simulation remain independent Python packages; preserve established package boundaries.
- Keep CRS explicit (`EPSG:4326`, `EPSG:3826`) and preserve provenance at boundaries.

## Development
- Respect repository OpenSpec specifications; use `guidance/openspec-workflow.md` for change routing.
- Scientific work follows Evidence → Assumptions → Model → Validation.
- Respect existing specifications; update them before changing public contracts or major assumptions.
- Verify behavior with targeted checks; report exact commands, results, and unverified limits.
- Before archiving an OpenSpec change, run `make openspec-gate CHANGE=<name>`; a failing gate blocks archive.
- Do not ingest live data, reset PostGIS, or expose or replace credentials.
- Do not alter shared/global agent configuration, or publish/push without authorization.
- Significant scientific assumptions or architecture changes require explicit human approval.

## Guidance
- Load only relevant role-specific instructions from `guidance/<role>.md`.
- `guidance/openspec-workflow.md` defines change routing and the evidence-driven lifecycle.
- `guidance/human-escalation.md` is OpenRig-specific; consult only when operating in OpenRig and escalation is needed.
