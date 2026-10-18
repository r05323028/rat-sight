# Tasks

## Evidence lifecycle

- [x] 1. Review prior source investigation and recheck Rat Radar, Taipei open-data, Taipei 1999, and relevant official sources using documentation/non-sensitive metadata only. Owner: science-researcher; artifact: `docs/evidence/rodent-report-source-investigation-2026-10-17.md`.
- [x] 2. Record claim-level URLs, verification dates, authority, access, licensing, privacy, spatial/temporal quality, semantics, uncertainty, and blockers. Owner: lead/research; artifact: `verification/source-comparison.md`.
- [x] 3. Obtain independent public-health/privacy and technical feasibility review. Owners: public-health and infrastructure; artifacts: `docs/evidence/rodent-report-public-health-suitability-review-2026-10-17.md` and source handoff findings.

## Recommendation

- [x] 4. Produce candidate comparison, suitability assessment, and explicit **NO-GO** for real download, ingestion, redistribution, and model use. Artifact: `evidence.md`.
- [x] 5. Define a concrete conditional next implementation contract and exact human decision owner. Artifact: `recommendation.md`; unknown contract fields block implementation.

## Verification and closure

- [x] 6. Obtain independent adversarial review and resolve all findings.
- [x] 7. Complete traceability and QA artifacts, run `openspec validate evaluate-real-rodent-data-sources` and the existing quality gate, and stop at Ready for Human Review.

## Explicit boundary

No task authorizes downloading raw citizen reports, scraping records, importing real data, modifying APIs/migrations/UI, or connecting data to simulation. Completion requires a final statement that no raw real records were accessed or stored.
