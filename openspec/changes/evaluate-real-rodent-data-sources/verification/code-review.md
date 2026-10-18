# Documentation/code review — evaluate real rodent data sources

**Reviewer:** verification-reviewer

**Scope:** documentation-only change: `proposal.md`, `design.md`, `specs/real-rodent-data-sources/spec.md`, `tasks.md`, `evidence.md`, `recommendation.md`, `verification/source-comparison.md`, and the adversarial review artifact. No application code, API, migration, dependency, fixture, or stored data changes are in scope.

**Decision: PASS** for the research-only feasibility scope.

## Independent checks

- `openspec validate evaluate-real-rodent-data-sources` — **valid**; only the existing long-requirement warnings remain.
- The spec uses an accepted `## ADDED Requirements` delta header and each requirement has a scenario.
- The source-comparison register contains candidate claims, URLs, verification date, status, limitations, and semantic/privacy consequences.
- `proposal.md`, `evidence.md`, and `recommendation.md` consistently state **NO-GO** for real download, ingestion, redistribution, and model use for every candidate.
- The proposed future contract explicitly treats unknown authorization, licensing, privacy, CRS/precision, semantics, retention, and update fields as implementation blockers.
- `tasks.md` defines metadata-only research, independent review, traceability, validation, human decision, and Ready for Human Review gates without implementation or raw-data-ingestion tasks.
- The artifacts consistently preserve distinctions among reports, observations, moderation, service requests, inspections, treatment, prevalence, movement, risk, and simulation.
- No real source access or authorization is claimed. The exact human decision remains with the project owner through the supported OpenRig gateway/queue.

## Findings

No remaining documentation or contract findings within this review boundary.

## Boundary statement

This PASS does not authorize any real-source download, scraping, storage, redistribution, ingestion, or model use. The current recommendation remains **NO-GO** until the explicitly named human decision and written source/privacy terms exist.
