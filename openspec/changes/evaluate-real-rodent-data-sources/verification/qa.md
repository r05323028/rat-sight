# Independent QA — evaluate-real-rodent-data-sources (research-only)

**Verdict: CLEAR** for the research-only feasibility scope. The lead-owned gate artifact was subsequently added and the quality gate passed.

- Qitem: `qitem-20261017190629-29389848762aa330`
- Evaluator: `verification.qa@rat-team`
- Candidate: documentation-only diff `openspec/changes/evaluate-real-rodent-data-sources` on
  `main` at `707af15`
- Date: 2026-10-17
- Scope: independent, read-only. No implementation code or data was edited, and no raw citizen
  records were accessed, downloaded, scraped, stored, or imported.

## Commands and results

| # | Command | Result |
|---|---------|--------|
| V1 | `openspec validate evaluate-real-rodent-data-sources` | **valid** (no validation errors) |
| V2 | `git diff --stat HEAD` | only `docs/evidence/rodent-report-source-investigation-2026-10-17.md` (+1/−1) and the prior `stabilize-.../verification/qa.md` evidence note |
| V3 | `git status --porcelain` filtered for `apps/`, `services/`, `packages/`, `scripts/`, `Makefile`, `*.py`, `*.ts(x)` | **NONE** — no application/API/migration/dependency/fixture/data changes |
| V4 | `make openspec-gate CHANGE=evaluate-real-rodent-data-sources` | **PASS** after lead added `verification/gate.json` (initial pre-artifact run was blocked only by the missing record) |
| V5 | claim register inspection | **9 claim IDs (`RDS-E01`…`RDS-E09`)**, each with URL, verification date, `VERIFIED`/`UNVERIFIED`/`BLOCKED` status, and limitation |
| V6 | raw-data indicator scan of the new change docs and public-health review | only prohibition/interface-description strings; **no raw rows, names, photos, addresses, or exact coordinates** present |
| V7 | prior smoke evidence re-check | `stabilize-rodent-report-integration/verification/qa.md` records the 2026-10-17 reruns: `make rodent-report-smoke` **PASS** both scenarios; `make geospatial-smoke` **PASS** 4/4 |

## Research content verified

- **Metadata-only method and no-download boundary:** the proposal, design, evidence,
  recommendation, public-health review, and source-comparison all restrict work to public
  documentation/non-sensitive metadata. Rat Radar's export endpoint is recorded as a
  metadata-only `HEAD`; the CSV was **not** downloaded. Each claim carries source URLs and the
  verification date 2026-10-17.
- **Claim-level comparison:** `verification/source-comparison.md` distinguishes Rat Radar,
  Taipei open-data, and Taipei 1999, and records authority, licensing, automated-retrieval,
  redistribution, privacy/retention, CRS/precision, coverage, schema, and update terms as
  `UNVERIFIED`/`BLOCKED` where not established. Negative portal search results are scoped to
  five exact keyword queries and are not treated as proof of absence.
- **Semantics preserved:** reports / platform moderation / `已通報1999` / service requests /
  inspections / treatment / confirmed observations are kept distinct; public moderation and
  1999 submission are explicitly not municipal confirmation or `OBSERVED`.
- **Explicit decision and human owner:** proposal, `evidence.md`, and `recommendation.md`
  consistently state **NO-GO** for real download, ingestion, redistribution, and model use for
  every candidate, and name the human project owner via the supported OpenRig gateway/queue as
  the decision maker. Agents are not authorized to grant raw access.
- **Conditional next contract:** `design.md`/`recommendation.md` give a concrete
  unknown-blocks-implementation checklist (identity/access, written permission, allowed fields,
  forbidden fields, semantics, spatial/temporal precision, validation/provenance, retention/
  update, API states). Unknowns block implementation.
- **Reviewer artifacts coherent:** adversarial review `PASS` (RDS-001…RDS-005 resolved) and the
  documentation code review `PASS`; both explicitly withhold any real-source authorization.
- **Traceability:** `verification/traceability.md` maps each requirement to its artifact and
  verification, with the no-application/data row marked `PARTIALLY_VERIFIED` pending QA — this
  QA pass supplies that evidence.

## No-download / privacy boundary confirmation

The original QA pass read only repository documentation and did not call Rat Radar,
the Taipei open-data portal, data.gov.tw, or any 1999 surface. A follow-up on 2026-10-17 made a
metadata-only HTTP `HEAD` to <https://1999.gov.taipei/>; it redirected to
<https://1999.gov.taipei/Front/main> and returned HTTP 200 (`text/html; charset=utf-8`). A
metadata-only `GET` confirmed page title `臺北市陳情系統1999` and a description identifying it as
Taipei City Government's petition and dispatch-case channel. This verified the service page only.
No complaint/report row, export, photograph, name, contact detail, description, exact address, or
exact coordinate was accessed, downloaded, stored, or imported. No real data was used in any check.

## Findings

### QA-RDS-001 — INFO — RESOLVED: `verification/gate.json` added

The initial pre-artifact run returned `GATE-RECORD-MISSING`; the lead then added
`verification/gate.json`. The subsequent `make openspec-gate CHANGE=evaluate-real-rodent-data-sources`
run passed. This was a lead-owned artifact omission, not a research finding.

### Standing repo hygiene (outside this change)

Untracked `.agents/skills/sem/**` and `skills-lock.json` keep repo-wide `ruff check .`
(13 E501) and `ruff format --check .` (4 files) red. Not related to this documentation-only
change.

## Limitations

- The QA is documentation-level. It does not independently re-contact any source; external
  facts rely on the recorded URLs/verification dates in the evidence artifacts.
- The `NO-GO` decision and the exact human authorization step remain with the project owner; QA
  does not and cannot authorize real-source access.

## QA position

The research-only feasibility change is internally consistent, claim-traceable, and
boundary-safe, with no code/data change and no real-record access. I return **CLEAR** for the
QA scope; the final quality gate also passes.
