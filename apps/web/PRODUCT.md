# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: Taipei municipal analysts working on urban rodent issues (health and environmental inspection teams), in a desktop browser, in Taiwan Traditional Chinese. Their job: find out which rodent-related data exists, how far each layer and result can be trusted, inspect Taipei geography and infrastructure context, run a controlled synthetic simulation preview, and judge whether any field action is supported.

Current situation: no verified Taipei rodent observation dataset is loaded. The analyst is evaluating the workspace's capability and its evidence boundaries, not concluding from real counts. The municipal persona used in the usability review is simulated, not an authenticated city employee (docs/rat-sight-first-black-box-usability-review.md).

## Product Purpose

RatSight is an evidence-aware urban rodent movement analysis workspace for Taipei. It shows available and missing datasets with their scientific classification, renders administrative districts and stormwater pipelines as reference layers on a Taipei map, and runs a deterministic seeded synthetic random-walk preview over a synthetic graph.

It exists because municipal rodent decisions are otherwise made without traceable provenance. Success means an analyst can tell, without prior knowledge, which layers are real reference data, which are simulated, which are absent, and which conclusions are prohibited — and that capability is never bought by presenting synthetic output as observation.

## Positioning

A provenance-first analysis workspace that grows into municipal decision support only as verified data arrives. The mechanism: every layer, feature, and simulation result carries an explicit class (OBSERVED, INFERRED, SIMULATED, UNVERIFIED) plus source, license, CRS, version, and assumptions at the point of use, and the workspace is built to display absence and non-estimation honestly. A neighbouring dashboard could copy the map; it could not copy that discipline without giving up the claims it wants to make.

## Operating Context

- Desktop browser against a single FastAPI service; Next.js, MapLibre, and TanStack Query dashboard; local PostgreSQL/PostGIS development database.
- Basemap: CARTO Positron (free, no key), configurable through NEXT_PUBLIC_MAP_STYLE_URL; provider attribution retained.
- Data arrives by local-file importers only — official Taipei administrative district boundaries (EPSG:3826 to EPSG:4326), stormwater pipeline data, and suppressed 250 m citizen-report aggregates — and is served through versioned JSON contracts. Map layer requests are viewport-bbox bounded.
- Local development: make db-up, make migrate, make api, make web; the dashboard is served at http://localhost:3000.
- Work is governed by the repository's evidence-driven OpenSpec workflow and by the OBSERVED / INFERRED / SIMULATED / UNVERIFIED contract in AGENTS.md.
- Analyst tasks observed in review: run the synthetic preview, inspect layers and feature attributes, review suppressed citizen-report aggregate cells, read the analysis panel.

## Capabilities and Constraints

- Layer catalog with availability state, classification badge, and per-layer status message (not imported, zoom required, service unavailable).
- Map panels: 圖層 (visibility controls), 行政區檢視 (ADMINISTRATIVE_REFERENCE, UNVERIFIED), 雨水下水道管線 (INFRASTRUCTURE_REFERENCE, UNVERIFIED, bounded bbox, allowlisted publisher attributes, no topology), 公民通報彙整 (CITIZEN_REPORT_AGGREGATE, UNVERIFIED, suppressed 250 m cells), 模擬預覽, 分析.
- Deterministic synthetic simulation preview carrying model id and version, parameters, random seed, synthetic provenance, assumptions, and node/edge visit counts with normalized frequencies; status SIMULATED.
- Constraints: no real Taipei rodent observations; no biological parameters, calibration, or model-accuracy metrics; no statistical summaries, risk estimates, or quantified uncertainty; simulated paths are never observed migration; stormwater connectivity is UNVERIFIED; source and target CRS stay explicit; importers are local-file only; no live data ingestion and no fabricated Taipei counts; the UI is Taiwan Traditional Chinese (zh-Hant) with the English classification tokens preserved verbatim.
- Repository-enforced scientific integrity (AGENTS.md): simulated rodent movement must never be presented as an observed migration or real-world event, and absence of data is not a zero count.
- Undecided: real observation acquisition and licensing, a risk or hotspot model, quantified uncertainty, report export, mobile layout, and multi-user roles.

## Brand Commitments

- Name: 見光鼠 RatSight; document title 見光鼠 RatSight · 都市鼠類移動分析.
- Voice: plain, declarative Traditional Chinese that states limits before capability; classification tokens remain English literals.
- No logo, palette, or visual identity is confirmed as binding; the incumbent look is evidence, not a commitment.

## Evidence on Hand

- docs/rat-sight-first-black-box-usability-review.md — black-box usability review using a simulated municipal persona; observed findings UX-001 to UX-003; screenshots were written to /tmp and are ephemeral; reproduced by an independent QA pass and bounded by a public-health interpretation review.
- docs/evidence/ — dated acceptance, feasibility, and source-investigation reports for Taipei district boundaries, the stormwater network, citizen-report source and public-health suitability, official complaint activity, and public trash bins. Historical reports describe the retired synthetic rodent-report fixture.
- Imported real reference data: official Taipei administrative districts and stormwater pipelines, each carrying dataset_id, resource version, license, attribution, archive SHA-256, and source/target CRS.
- Synthetic simulation fixture: the seed-42 preview reproducibly reports 312 node visits and 16 synthetic edges over a schematic graph; it is a movement-mechanics demonstration, not an observed rodent layer.
- Citizen-report aggregate layer: suppressed 250 m cell × month × report-type counts only; UNVERIFIED, attributed, and never rendered as observations, abundance, or movement. Real aggregate-cell simulation origins remain disabled in the UI pending approval gates.
- Absences future work must not fill by invention: no real rodent observations, no prevalence/incidence/population estimates, no validated model accuracy, no quantified uncertainty, and no municipal endorsement or deployment.

## Product Principles

1. Classify before display — the evidence class travels with the datum, at the point of use.
2. Unknown is not zero — unavailable data, unestimated uncertainty, and absent observations are stated as such.
3. Simulation demonstrates, it does not forecast — seeded, versioned, reproducible, and labelled SIMULATED wherever it appears.
4. Capability grows with evidence — no analysis surface ships ahead of the verified data that would justify it.
5. Provenance stays inspectable — source, license, CRS, version, hash, and processing steps remain reachable from the interface.
