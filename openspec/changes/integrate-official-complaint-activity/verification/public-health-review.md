# Public-health review — official complaint activity feasibility

**Review date:** 2026-10-18  
**Review boundary:** Independent review of `docs/evidence/official-complaint-activity-feasibility-2026-10-18.md` and the active proposal/design/spec/tasks. No additional raw-record access was performed.  
**Decision:** **NO-GO for implementation and rodent analytics.** The NO-GO is correctly supported by the current evidence.

## Evidence and status

The feasibility artifact identifies Taipei City dataset `cb423c17-88eb-4231-a725-f1b93247d1bf`, resource `b57a0fa8-9507-438b-b2e1-676829a72aff`, detail URL <https://data.taipei/dataset/detail?id=cb423c17-88eb-4231-a725-f1b93247d1bf>, and resource URL <https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=b57a0fa8-9507-438b-b2e1-676829a72aff>. The artifact records checks on 2026-10-18 (Asia/Taipei), Government Data Open License v1 metadata, and temporary analysis only. These establish a candidate official administrative source, not rodent observations or authorization for RatSight storage/publication.

The source is suitable for further metadata/data-owner clarification only. It is not currently suitable for code, model, or dashboard implementation.

## Findings

### 1. Category specificity — decisive NO-GO

The inspected resource has primary and secondary complaint categories and receiving offices, but no `鼠`, `rodent`, `rat`, or `病媒` category value in either category field. Values such as parks/drainage/sewer/water, animal protection/rescue, drainage clearing, stormwater/wastewater maintenance, road cleaning, and a vector-control receiving office are broad administrative classifications. None defensibly identifies a rodent complaint.

A receiving office such as `水質病媒管制科` indicates routing/organizational responsibility, not complaint subject, species, or confirmation. The artifact correctly sets the exact rodent mapping to empty/unknown and forbids fuzzy matching. This is sufficient for NO-GO; no rodent aggregate may be derived from these categories.

### 2. Complaint versus observation semantics — preserved and correct

A row is a complaint-system case/category record, not a sighting, inspection finding, treatment record, confirmed observation, prevalence measure, or population count. `受理日期`, `送達日期`, and `結案日期` describe administrative workflow timing; they do not establish animal event time. Missing `結案日期` means unresolved workflow state, not ongoing rodent activity.

The proposal/design/spec correctly require administrative complaint semantics and prohibit `OBSERVED`, prevalence, intervention, movement, and risk claims. Any future qualified output must retain original category and explicitly say “complaint activity,” never “rodent presence.”

### 3. Record grain and duplicates — implementation blocker remains

The temporary analysis found 42,674 non-empty unique `案件編號` values in the inspected resource, but the artifact correctly says one row per case/category and cross-month longitudinal grain must be confirmed by the publisher’s data dictionary. Per-file uniqueness does not establish uniqueness across monthly resources, correction behavior, category changes, or whether a case can appear in multiple category rows.

Until record grain, stable identity, monthly overlap, corrections, and deletion behavior are documented, no longitudinal count or deduplication rule should be implemented. If a future GO is granted, independent source-total comparison and explicit duplicate/exclusion accounting are required.

### 4. Privacy and licensing — aggregate-only, not yet authorized for implementation

The inspected schema contains no names, free text, photos, coordinates, or addresses, which is a positive minimization property. However, case IDs and fine-grained workflow timestamps may remain linkable, especially when combined with other sources. Individual complaint IDs and row-level timestamps must not be persisted or exposed. A future aggregate must use approved time granularity and access/retention controls.

Portal metadata reports `公開` and Government Data Open License v1. This is useful evidence, but the applicable current license text, attribution, dataset-specific restrictions, and permitted storage/redistribution scope still require confirmation at implementation time. “Open” does not authorize re-identification, semantic relabeling, or unrestricted raw retention.

### 5. Spatial and temporal suitability — no spatial layer possible

The resource has no latitude, longitude, address, district, geometry, or CRS. A municipal label must not be used as an incident location or geographic proxy. The proposed design correctly forbids geographic filtering and location claims unless a future verified resource supplies spatial fields.

The observed date strings and monthly packaging support workflow activity only. Resource names/month labels must not be silently converted from ROC-style values or interpreted as calendar coverage without publisher confirmation. A future descriptive aggregate would require documented timezone, bucket, inclusive/exclusive boundaries, corrections, and missingness.

## Required exclusions

Until a new authored gate resolves the blockers, exclude:

- all rodent-specific counts or mappings from this resource;
- fuzzy matching of categories, offices, or text to infer rodents;
- relabeling complaints as sightings, observations, infestation, prevalence, incidence, risk, hotspots, or population;
- geographic display/filtering or inferred complaint locations;
- use as simulation movement weights, biological parameters, infrastructure connectivity, disease evidence, or intervention-effect evidence;
- persistence or exposure of raw CSV rows, case IDs, individual dates, or any future personal/free-text fields;
- longitudinal deduplication or trend claims before record-grain/version/correction semantics are verified.

## Conditional future GO criteria

A separate human/data-owner decision is required before any implementation. It must establish all of the following:

1. Exact official rodent category mapping or an explicit decision that this dataset is not a rodent source.
2. Publisher-confirmed record grain, cross-resource identity, duplicates, corrections, deletions, and update/version rules.
3. Current license text, attribution, storage/redistribution permission, retention, access, and disclosure controls.
4. Approved monthly or coarser time aggregation and small-cell suppression; no individual case exposure.
5. A non-spatial aggregate contract retaining administrative complaint semantics and uncertainty.
6. Independent public-health/privacy acceptance and deterministic source-total validation.

If these criteria are met for a non-rodent contextual product, it must be separately scoped as `COMPLAINT_ACTIVITY`/administrative data. It must remain disconnected from rodent observations, simulation, infrastructure topology, prevalence, risk, and causal analysis. If an exact rodent mapping is not supplied, the outcome remains NO-GO.

## Review conclusion

The feasibility artifact's NO-GO is correct and should be accepted as a complete Phase-A research deliverable. No implementation, migration, API, UI, or model change is authorized by this review. `git diff --check` and `openspec validate integrate-official-complaint-activity` should be run by the coordinator after this artifact is added.
