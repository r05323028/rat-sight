# Evidence: Taipei stormwater network candidates

- Evidence ID: `EVID-TPE-STORMWATER-NETWORK-2026-10-16`
- Data class: `ADMINISTRATIVE_REFERENCE` / infrastructure reference candidate; not rodent observations and not verified physical connectivity
- Retrieved: 2026-10-16 UTC (metadata and files retrieved at approximately 16:56–16:58 UTC)
- Publisher/agency: Taipei City Government Public Works Department, Water Resources Division (臺北市政府工務局水利處) for Candidate A; Taipei City Government Public Works Department (臺北市政府工務局) for Candidate B
- License as displayed: public/open; both pages link Taipei's Government Open Data License v1 at https://data.taipei/rule (also https://data.gov.tw/license). The license grants non-exclusive, irrevocable, royalty-free use without purpose/time/territory limits, including reproduction, distribution, transmission, editing and derivative works; it requires compliance with the terms and the prescribed attribution statement.

## Candidate A

- Dataset UUID: `83048de2-7305-45e4-b022-e04c5155978e`
- Metadata URL: https://data.taipei/dataset/detail?id=83048de2-7305-45e4-b022-e04c5155978e
- Resource download URL: https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=ab39d90d-19aa-4027-844c-f07a12c34ca8
- Page title: 臺北市雨水下水道管線資料
- Description: 管線圖資及屬性資料 KML 檔案格式
- Resource label: 臺北市雨水下水道管線屬性資料表 KML 檔格式
- Format: KML/XML; response was HTTP 200, `Content-Type: text/xml;charset=UTF-8`, `Content-Length: 29401672`, filename `雨水下水道管線.kml`
- Download SHA-256: `afceac2cf8289166129e82cd34f568a2efcdbfd0e81807e8aba7300a0ffeefcd`
- Metadata: Water Resources Division; public data authorization; irregular update; collection period displayed as 2020-07-14 through 2025-06-09; metadata updated 2026-06-25 16:08:40; resource updated 2026-06-25 16:08:24.
- Structure: 17,408 KML `Placemark` records; each has a 2D `LineString` under `MultiGeometry`; 22 `SimpleData` fields including pipe number, catchment, type, material, dimensions, length, slope, elevations, cover depth, creator and creation date.
- Coordinate inspection: coordinates are longitude/latitude decimal pairs in KML (`121.464153241866` to `121.623632758854`, `24.9755398222327` to `25.1438747058009`). KML convention is an inference from the format and values; the downloaded file did not provide an explicit CRS declaration that was independently resolved to an EPSG code.
- Quality checks: all 17,408 records had a non-empty `管線編號`; 17,408 constructed LineStrings were valid; six pipe-number values were duplicated (17,401 unique IDs). Some attributes are empty: upstream/downstream elevations (19–20), cover depths (19–34), pipe count (50), and widths (2–36), depending on field.

## Candidate B

- Dataset UUID: `97b82d58-faba-4ee4-9488-dd5d04a79efd`
- Metadata URL: https://data.taipei/dataset/detail?id=97b82d58-faba-4ee4-9488-dd5d04a79efd
- Resource download URL: https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=5240223d-5187-454e-b323-63443a195639
- Page title: 臺北市公共管線圖資_雨水系統管線
- Description limitation: the publisher states that the network map is for reference only and that exact data should be obtained from the relevant utility agency.
- Resource label: 臺北市公共管線圖資_雨水系統管線 XML 檔案格式
- Format: XML/GML-like utility schema; response was HTTP 200, `Content-Type: text/xml;charset=UTF-8`, `Content-Length: 25086504`, filename `A8040201_11502.xml`
- Download SHA-256: `5d2ea04f7d032d21b07066310e80eb64a34ce8916b4a0c786b10948aeb4e10e4`
- Metadata: Public Works Department; public data authorization; irregular update; metadata updated 2026-10-15 13:44:12; resource updated 2026-02-23 17:10:41.
- Structure: 19,747 `UTL_管線` records; every inspected record had a 3D GML `LineString` with `srsName="EPSG:3826"` and `srsDimension="3"`; fields include geometry, category code, identifier, start/end node numbers, managing unit, work classification, installation date, pipe number, dimensions, material, length, type, use status, data status and notes.
- Coordinate inspection: EPSG:3826 coordinates ranged from X `296751.659` to `313576.48` and Y `2763230.291` to `2785982.166`; all constructed 2D projections of the 3D line strings were valid LineStrings with at least two points. The third coordinate was retained in the source and not interpreted as a network/topology claim.
- Quality checks: all 19,747 `識別碼` values were non-empty and unique (the selected source-record key); 20 records had empty `管線編號`; 311 pipe-number values were duplicated (19,380 unique non-empty IDs); 991 endpoint-start and 991 endpoint-end values were empty (counts overlap partially); 17,950 notes were empty. These are source quality findings, not repair recommendations.

## Selection recommendation

Select **Candidate B as the MVP source candidate**, not as certified infrastructure truth. It has an explicit source CRS (`EPSG:3826`), a structured utility schema, explicit start/end node fields, and a publisher warning that the map is reference-only. Its missing and duplicate identifiers must be surfaced and handled before any import contract treats identifiers as keys. Candidate A has richer measured/attribute fields and all non-empty pipe numbers, but its KML CRS is implicit and six pipe-number duplicates remain; accepting it would require an explicit CRS interpretation/validation step.

The MVP boundary should initially preserve raw line features and source attributes with provenance. It must not infer physical connectivity from line intersections, endpoint proximity, or surface geometry. Endpoint fields may be retained as source attributes, but graph edges and movement/topology semantics require engineering/source-owner review. Neither candidate is rodent observation data, and neither supports claims about rodent movement, sewer completeness, or intervention effects.

## FACT / INFERENCE / UNVERIFIED

### FACT

- Both metadata pages and both download URLs were available with HTTP 200 on 2026-10-16 UTC.
- Candidate A and B hashes, filenames, sizes, formats, record counts, geometry types and quality counts are recorded above from the downloaded temporary files.
- Candidate B embeds `EPSG:3826` in each sampled/inspected GML LineString; Candidate A is KML with longitude/latitude coordinate values but no independently resolved EPSG declaration in the file.
- Both publishers identify the datasets as public/open and provide irregular-update metadata. Candidate B explicitly limits use to reference purposes.

### INFERENCE

- Candidate B is the stronger MVP intake candidate because explicit CRS and source endpoint fields reduce ambiguity, despite quality defects.
- Candidate A coordinates are likely EPSG:4326 because KML coordinates follow the KML longitude, latitude order and fall within Taipei-like geographic ranges; this is not a source-declared CRS fact.
- A single source version should be immutable by URL, retrieval timestamp and hash; this is a reproducibility recommendation, not evidence that either source is complete or current.

### UNVERIFIED / LIMITATIONS

- Legal/engineering currency and completeness of either network are not established. Both update irregularly; Candidate B's resource predates its metadata update.
- The publisher's reference-only warning means Candidate B cannot be treated as an authoritative physical network without agency confirmation.
- Attribute definitions, identifier semantics, duplicate-row causes, missing-ID causes, vertical datum/third-coordinate meaning, network topology rules, and coverage boundaries need source-owner or engineering review.
- No comparison against official as-built records, field verification, or network completeness assessment was performed.
- No data was written to the database and no implementation was changed.

## Reproducibility record

Downloads were made with `curl -L` to temporary files on 2026-10-16 UTC. XML was parsed locally with Python's standard XML parser; LineStrings were constructed for geometry validity and coordinate-range checks. Raw files were not added to the repository. The hashes above identify the exact downloaded bytes used for these checks.
