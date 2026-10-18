# Independent QA — integrate-official-complaint-activity

**Verdict: CLEAR for Phase A NO-GO research scope.** No implementation is authorized because the verified source cannot defensibly isolate rodent complaints.

- Evaluator: verification.qa@rat-team
- Date: 2026-10-18
- Scope: metadata/source feasibility and research artifacts only; no code edits and no raw complaint data accessed by QA.

## Evidence and commands

| Check | Result |
|---|---|
| `openspec validate integrate-official-complaint-activity` | PASS / valid |
| Research artifact inspection | PASS: dataset/resource identity, license, resource metadata, schema, encoding, category values, record grain, dates, missing values, coverage, and NO-GO are documented in `docs/evidence/official-complaint-activity-feasibility-2026-10-18.md`. |
| Independent public-health/privacy review | PASS: `verification/public-health-review.md`; no defensible rodent mapping, no location fields, workflow timestamps not biological times, and case-ID/privacy limitations recorded. |
| Independent adversarial review | Conditional PASS findings addressed: OCA-001/OCA-002 resolved; OCA-003 recorded honestly as an accepted evidence limitation because the temporary file was deleted without checksum computation. |
| No-code/no-data boundary | PASS: no application, migration, API, UI, dependency, fixture, or stored complaint data changes. No raw CSV committed or retained. |
| Source-access boundary | PASS: researcher temporarily inspected the public CSV for schema/value feasibility, deleted it afterward, and did not persist rows. QA did not re-access raw data. |
| Prior regression evidence | PASS: prior stabilization QA records `make rodent-report-smoke` both scenarios and `make geospatial-smoke` 4/4 passed. |

## Feasibility conclusion

The official dataset is complaint-system activity, not confirmed observation data. The inspected resource has no rodent-specific category values, no location fields, and broad vector-control/drainage/animal labels that cannot be mapped to rodents. Therefore the correct result is **NO-GO** for rodent complaint ingestion, API/UI exposure, geographic analysis, simulation use, or model use.

A future separate contextual complaint-activity scope requires human/data-owner approval, a category dictionary or official crosswalk, verified record-grain/version semantics, privacy review, and an approved aggregate contract.

## Limitations

The temporary CSV content hash was not computed or retained before deletion. This is explicitly recorded in the feasibility artifact; future authorized retrieval must record exact byte count and SHA-256 before analysis. This limitation does not change the NO-GO decision.

No human project-owner acceptance is claimed.
