# Proposal

## Why

RatSight currently exposes only a synthetic rodent-report fixture. A real-data phase requires evidence of authority, lawful reuse, privacy safety, technical access, and scientific meaning before any download or ingestion.

Prior evidence: `docs/evidence/rodent-report-source-investigation-2026-10-17.md`.

## What Changes

- Investigate Rat Radar, Taipei open-data, Taipei 1999 complaints, and relevant official alternatives using public metadata and documentation only.
- Record verified findings, uncertainty, blockers, and source-specific semantics in an evidence comparison.
- Recommend either a bounded next integration target or explicit NO-GO.
- Define a proposed implementation contract without changing application code, APIs, migrations, dependencies, or stored data.

## Current recommendation and human decision owner

**Current recommendation: NO-GO for real download, ingestion, redistribution, and model use for every candidate.** Rat Radar is only the most promising future discovery candidate; Taipei open-data and 1999 remain unverified. The human project owner, reached through the supported OpenRig human gateway/queue, must explicitly choose one of: (a) NO-GO and close this research phase, or (b) authorize a bounded data-owner contact/metadata clarification step. No agent may authorize raw access, redistribution, or implementation.

## Integrity Boundary

This is research only. No raw citizen records, photographs, descriptions, names, exact addresses, or exact report coordinates may be downloaded, stored, or imported. Reports remain distinct from observations, inspections, treatment, prevalence, and causal evidence. No model, risk score, heatmap, or simulation input is created.
