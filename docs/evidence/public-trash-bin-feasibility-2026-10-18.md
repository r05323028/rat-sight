# Feasibility gate: Taipei public trash-bin layer

**Verification date:** 2026-10-18 (Asia/Taipei)

## Decision

**Phase A feasibility/reference proposal supported; implementation is CONDITIONAL NO-GO.** The source has Taipei point-like values but publisher CRS/axis order is unresolved, and no implementation, transformation, or resource selection is authorized. It is not currentness-complete: the catalog's collection end date is 2018-01-10 while metadata/resources were updated in 2026. Any future implementation requires preserving this limitation and `UNVERIFIED` currentness.

## Source identity and metadata

- **Dataset:** `a835f3ba-7f50-4b0d-91a6-9df128632d1c`, [Taipei City Data Platform detail page](https://data.taipei/dataset/detail?id=a835f3ba-7f50-4b0d-91a6-9df128632d1c).
- **Title:** `臺北市行人專用清潔箱` (Taipei pedestrian-use public cleaning bins).
- **Provider:** Taipei City Environmental Protection Department (`臺北市政府環境保護局`).
- **Portal license:** `公開`; retain the portal's Government Data Open License terms and required attribution. No personal data was observed in the fields.
- **Catalog metadata:** topic 環保; primary fields 行政區, 地址, 經度, 緯度, 備註; collection start `2014-12-25`, collection end `2018-01-10`; update frequency 不定期更新; metadata update `2026-09-30 15:55:47`.
- **Resource A:** `臺北市行人專用清潔箱`, resource ID `267d550f-c6ec-46e0-b8af-fd5a464eb098`; [download URL](https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=267d550f-c6ec-46e0-b8af-fd5a464eb098); portal displayed CSV, 62.05 KB, update `2026-09-30 15:55:35`.
- **Resource B:** `行人專用清潔箱總表（景點商圈周邊130點）`, resource ID `2030d728-9597-437d-81a4-cf2a44c7f114`; [download URL](https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=2030d728-9597-437d-81a4-cf2a44c7f114); portal displayed CSV, 5.27 KB, update `2026-08-18 16:27:22`.

The two resources are distinct publisher tables; they must not be blindly unioned because the second is explicitly a 130-point tourist/commerce subset and has different notes/coverage.

## Download integrity and encoding

Temporary official CSVs were downloaded only for this analysis and deleted afterward. No raw file is in Git or project storage.

| resource | exact bytes from local temporary file | SHA-256 |
|---|---:|---|
| A `267d...eb098` | 63,540 | `ff3cf5528c057958f89871aa5300fc633b02d0f7b37131ab29d5ddc2f8e2370d` |
| B `2030...7f114` | 5,396 | `47b1ddfb4f0ab4d5e57afab538f71da3d41d22e59c984bdd9c10b4248223b066` |

Both files were CSV with Traditional Chinese encoded as Big5/CP950; UTF-8 decoding failed. The first bytes did not contain a UTF-8 BOM. A future importer must specify `cp950` explicitly and retain the source encoding in provenance.

## Schema and validation results

Both resources have exactly these columns, in this order: `行政區`, `地址`, `經度`, `緯度`, `備註`.

### Resource A

- 681 rows.
- No null/blank values in any of the five fields.
- 11 distinct districts; 679 distinct addresses; one note value.
- 669 distinct longitudes and 671 distinct latitudes.
- One exact duplicate coordinate pair (coordinates are not a row identity).
- 680 coordinate pairs were numerically within the Taipei check envelope used for this analysis. One longitude was malformed as `?121.595369` (row address: 指南路3段40巷8-4號對面停車場 (貓空公車壺穴站)-1); latitude was `24.968972`. This must fail strict coordinate validation or go to an explicit quarantine/unavailable state; do not silently strip `?`.
- Valid numeric longitude range among parseable values: 121.466267–121.617093; latitude range: 24.965694–25.142327.

### Resource B

- 130 rows, matching the resource title's stated 130-point scope.
- No null/blank values in any field.
- 12 distinct districts; 123 distinct addresses; 22 distinct note values.
- No malformed coordinates under the same finite Taipei envelope check. Numeric longitude range: 121.464–121.617; latitude range: 24.968–25.155.
- Ten duplicate coordinate pairs; therefore coordinates are not a stable row identity. Exact full rows were unique in both resources.

### Overlap and identity

- Exact `(經度, 緯度)` overlap between A and B: 0.
- Exact address overlap: 0.
- Exact `(行政區, 地址)` overlap: 0.
- The tables are therefore non-overlapping under these exact comparisons, but this does not prove geographic non-overlap because address/coordinate normalization and rounding can differ.
- Neither resource supplies an explicit stable ID, source version ID per row, date field, or last-verified timestamp. A future system may derive an opaque deterministic `source_record_id` from dataset/resource ID plus canonical source-row content, but no MVP resource is selected. Canonicalization must be specified before implementation: UTF-8 after CP950 decoding; Unicode NFC; trim and collapse ASCII whitespace only where the source contract permits; preserve field order; length-prefix each field to avoid delimiter ambiguity; preserve coordinate lexical text until strict numeric validation; hash `dataset_id\nresource_id\nfield_count\n[field_length:field_bytes...]` with SHA-256; reject canonicalization collisions or malformed encodings. The result is technical and source-scoped, never an official facility ID; edits can create a new identity.

## Interpretation and limits

- These are public cleaning-bin locations, not waste volume, food availability, rodent sightings, pest-control records, or observed animal activity.
- The coordinates are publisher-provided point locations; source CRS is not declared in the inspected metadata. Coordinate values look like WGS84 longitude/latitude, but this is an inference and must remain `UNVERIFIED` until the publisher confirms CRS/axis order.
- Resource A's malformed longitude and duplicate coordinates require quality flags. Resource B's repeated coordinates may represent multiple bins or rounded/shared locations; no deduplication should be inferred.
- Catalog currentness is unresolved: collection end 2018-01-10 conflicts with 2026 resource/metadata update timestamps. Resource update is not proof that every location was surveyed or current.
- Exact addresses and coordinates can facilitate physical targeting or inference about facilities. Although no personal fields were present, retain only what the approved use needs, avoid joining with citizen reports, and apply ordinary access/privacy review.
- No relationship to rat abundance or movement can be claimed without independently collected, validated rodent observations and a pre-specified model.

## Recommendation / implementation gate

Proceed only with a separate human-approved infrastructure-reference decision that explicitly selects Resource A or Resource B (or keeps both separate), and then:

1. stores source and resource IDs, retrieval timestamp, byte size/hash, encoding (`cp950`), publisher attribution/license, and `classification=UNVERIFIED`;
2. requires explicit CRS confirmation or labels CRS as unknown (no silent EPSG:4326 claim);
3. rejects/quarantines malformed coordinates such as the `?121.595369` value and records the quality count;
4. keeps Resource A and B as separate layers/coverage sets unless a source-owner crosswalk authorizes a merge;
5. displays the layer as public cleaning-bin reference data, never as rodent evidence or risk;
6. documents the 2018 collection-currentness limitation and does not imply update completeness.

No code, migration, API, UI, or simulation change is authorized by this Phase A feasibility artifact.
