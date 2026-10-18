# Feasibility gate: official Taipei complaint activity dataset

**Verification date:** 2026-10-18 (Asia/Taipei page/resource checks)

## Decision

**NO-GO for rodent activity ingestion or model use.** The dataset is a useful official complaint-activity source for a future, separately scoped service-request analysis, but this verified resource contains no defensible rodent category mapping. It has no location fields, and its records are complaint-system activity rather than confirmed sightings or biological observations. Do not use it as rodent observations, prevalence, movement weights, or intervention evidence.

## Source identity and access

- **Dataset:** `cb423c17-88eb-4231-a725-f1b93247d1bf`, [Taipei City Data Platform detail page](https://data.taipei/dataset/detail?id=cb423c17-88eb-4231-a725-f1b93247d1bf).
- **Title:** `臺北市陳情系統類別資料` (Taipei City petition/complaint system category data).
- **Provider:** Taipei City Research, Development and Evaluation Commission (`臺北市政府研究發展考核委員會`, 研考會).
- **Classification on portal:** original data; subject category 民政; service category 公共資訊.
- **License:** portal displays `公開` and `依政府資料開放授權條款-第1版` (Government Data Open License v1). Preserve attribution and license terms; “open” does not authorize re-identification or changing complaint semantics.
- **Access:** public detail page and public CSV download/resource preview. No login was required for metadata or the CSV resource used for temporary schema/value analysis. The raw temporary file was deleted after analysis and was not committed or persisted.
- **Latest inspected resource:** `11509案件類別趨勢明細表`, resource ID `b57a0fa8-9507-438b-b2e1-676829a72aff`, [download URL](https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=b57a0fa8-9507-438b-b2e1-676829a72aff). Portal displayed CSV, UTF-8, approximately 6.73 MB, resource update `2026-10-08 15:47:05`.
- The page lists monthly resources (including 11509, 11508, 11507, 11506); the dataset metadata states monthly update frequency and collection period `2016-11-01` through `2026-09-30`. Resource-level date values should be treated as publisher-provided strings and checked against each resource version; do not silently infer calendar conversion from ROC-style resource names.

## Schema and temporary value analysis

The inspected CSV header, in order, is:

`案件編號`, `案件主類別`, `案件次類別`, `受理機關`, `受理科室`, `受理日期`, `送達日期`, `結案日期`

Observed in the latest resource:

- 42,674 rows; 8 columns; UTF-8 BOM (`utf-8-sig`) CSV.
- `案件編號` was non-empty and unique in all 42,674 rows checked; no duplicate IDs were found.
- `案件主類別`: 10 distinct values; no missing values.
- `案件次類別`: 133 distinct values; no missing values.
- `受理機關`: 138 distinct values; no missing values.
- `受理科室`: 396 distinct values; 4,542 missing values.
- `受理日期`: no missing values; values were 15-character strings of the form `YYYYMMDDThhmmss` in this resource. Observed lexical range: `20260721T210045`–`20261005T111554`.
- `送達日期`: no missing values; same 15-character form. Observed range: `20260901T000042`–`20260930T235705`.
- `結案日期`: 1,748 missing values; non-empty values used the same 15-character form. Observed range: `20260901T003106`–`20261007T165236`.
- The portal metadata lists primary fields as case ID, primary/secondary category, receiving agency/office, and received/delivered/closed dates. There are no latitude, longitude, address, district, geometry, free-text description, photo, species, observation-method, or confirmation fields in this resource.

These are structural findings from temporary analysis of the public resource, not retained complaint records or RatSight observations. The temporary file was deleted after analysis; an exact byte count and SHA-256 were not computed or retained, so these findings are tied to the resource ID, URL, portal update timestamp, and retrieval date rather than a reproducible content hash. Any future authorized retrieval must record exact byte count and SHA-256 before analysis, then delete the raw file.

## Category values and rodent mapping

No `鼠`, `rodent`, `rat`, or `病媒` value occurred in either category field in the inspected resource. Relevant-looking values that **were present** included:

- Primary category `公園、排水溝、下水道及自來水` (parks, drainage ditches, sewers and water supply).
- Secondary categories `動物保護` (animal protection), `動物救援（派工）` (animal rescue dispatch), `排水溝疏通` (drainage ditch clearing), `雨水下水道維護` (stormwater sewer maintenance), `污水下水道維護（含孔蓋冒水）、污水管申接、污水排放稽查` (wastewater sewer maintenance/connections/discharge inspection), and `路面清潔（含行人果皮箱、菸蒂、狗便）` (road cleaning, including bins/cigarette butts/dog waste).
- Receiving offices include `水質病媒管制科` (water-quality/vector-control section), cleaning teams, and animal-protection offices.

None of these values is a defensible rodent mapping: they are broad service categories or receiving-office labels and do not identify the complaint subject. A “vector-control” office assignment does not prove a rodent report; drainage/cleaning/animal categories are not rodent observations. The exact defensible mapping from this resource is therefore **empty/unknown**. Any future mapping requires the data owner’s category dictionary or a controlled official crosswalk, with independent review.

## Spatial, temporal, privacy, and scientific limitations

- **Spatial:** no spatial field is present; no location, address, district, or CRS can be derived. Spatial analysis is impossible from this resource alone.
- **Temporal:** monthly resource packaging and the three case timestamps support complaint workflow timing only. They do not establish event time, observation time, or biological activity time. Missing closure dates represent unresolved workflow state, not ongoing rodent activity.
- **Record grain:** one row appears to be one complaint-system case/category record, identified by `案件編號`; this must be confirmed against the publisher’s data dictionary before longitudinal deduplication across monthly files.
- **Scientific meaning:** cases are administrative complaints/service activity. They are not sightings, inspections, confirmed species records, treatment records, prevalence, or causal evidence. Reporting access, routing, category changes, duplicates across monthly extracts, and agency workflow create substantial observation-process bias.
- **Privacy:** the inspected resource is category/date/agency data and did not expose names, free text, photos, or coordinates. Nevertheless, case IDs and fine-grained timestamps are potentially linkable identifiers. Apply minimization, access control, retention limits, and disclosure review before any project storage or publication. Do not combine with other sources to re-identify complainants.
- **License/reuse:** retain the portal’s Government Data Open License v1 and attribution. Confirm the current license text and any dataset-specific restrictions at ingestion time.

## Recommendation and blockers

1. **Do not proceed** with rodent ingestion, API/UI exposure, or model integration from this dataset.
2. If the product later needs official complaint activity as a non-rodent contextual layer, obtain human approval for a separate scope and preserve `ADMINISTRATIVE/COMPLAINT_ACTIVITY` semantics, source/resource IDs, monthly version, license, and uncertainty. Prefer aggregated counts by coarse time/administrative unit only if a future resource supplies an approved location dimension.
3. Before any rodent-specific use, require the publisher to provide: category dictionary/crosswalk, record-grain and versioning rules, spatial fields and CRS (if any), observation-vs-workflow definitions, privacy/retention terms, and an official statement distinguishing rodent complaints from vector-control, drainage, waste, and animal-service cases.
4. No code, migration, API, UI, or model change is authorized by this feasibility gate.
