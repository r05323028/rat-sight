# Human acceptance record

Status: **PENDING — no human decision recorded.**

## Decision packet

- **Question:** Should `sighting` be the only eligible citizen-report origin category, with `bait_station` and `other` context-only, for the bounded simulation workflow?
- **Recommended option:** Approve the conservative policy as implemented (`origin-report-category-v1`), keeping every input UNVERIFIED and every output SIMULATED.
- **Supporting evidence:** `docs/evidence/citizen-origin-eligibility-policy-2026-10-27.md`; enforced centrally in `services/api/src/ratsight_api/domain/citizen_report_aggregates.py`; rejected server-side in `services/api/src/ratsight_api/api/routes/simulations.py` (422 ORIGIN_REPORT_TYPE_INELIGIBLE); UI explanation and disabled action verified in dashboard tests and browser smoke.
- **Alternatives:** (a) admit bait-station reports as origins (rejected: bait is not an animal signal); (b) admit all categories behind a disclosure label (rejected: semantics are undefined); (c) no citizen-report origins until full scientific review (safe but removes the delivered workflow).
- **Consequences of approval:** the workflow ships with a documented, versioned, conservative policy; later expansion requires a new policy version and review.
- **Consequences of not approving:** the change stays blocked for human review and cannot be archived.
- **Specific decision required:** APPROVE / REJECT the `origin-report-category-v1` policy, with approver name, reference, and scope.

No approver, reference, or acceptance is fabricated by this record.
