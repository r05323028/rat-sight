# Evidence: Taipei administrative district boundaries

- Evidence ID: EVID-TPE-DISTRICT-BOUNDARIES-2026-10-15
- Data class: ADMINISTRATIVE_REFERENCE (official administrative reference record; not rodent observations)
- Epistemic classification: UNVERIFIED for currentness, because the resource is dated 2022-09-15 and legal currency after that version was not established
- Retrieved: 2026-10-15 UTC
- Canonical metadata: https://data.gov.tw/dataset/121199
- Publisher: Taipei City Government Department of Civil Affairs (臺北市政府民政局)
- Dataset identifier/title: 121199 / 臺北市區界圖
- Resource: 臺北市區界圖_20220915, SHP
- Download: https://data.taipei/api/dataset/1601ef3a-c253-4988-b047-943d9e786143/resource/d8b7eb29-136f-49fc-b14b-3489d3656122/download
- Archive SHA-256: `77bcc347b503b8ff8a43f7e1afaaedb18877a6222282587b145adaba69afd2d9`
- License: 政府資料開放授權條款-第1版; metadata license https://data.gov.tw/license. The terms permit reproduction, distribution, transmission and derivative works subject to attribution/terms.
- Metadata publication/update: metadata page reports irregular updates and was updated 2026-10-13; resource label/version remains 20220915.
- Source CRS: metadata says TWD97; the downloaded `.prj` and file inspection identify EPSG:3826 (TWD97 / TM2 zone 121).
- Coverage and attributes: 12 records, all Polygon, all valid, no null/empty geometries, unique CPID values, district names in `TNAME`, and identifiers in `COUN_ID`/`CPID`/`CPTID`.
- File bounds: EPSG:3826 `[296266.0530, 2761514.8960, 317197.2607, 2789176.1694]`.
- Processing observations: unary union is one Polygon; sum-vs-union area differs by approximately 1.23 m². This is not a legal completeness proof.

## Reproducible verification record

The following commands were run against the linked bytes on 2026-10-15 UTC:

```text
curl -L --max-time 60 -o source https://data.taipei/api/dataset/1601ef3a-c253-4988-b047-943d9e786143/resource/d8b7eb29-136f-49fc-b14b-3489d3656122/download
sha256sum source
# 77bcc347b503b8ff8a43f7e1afaaedb18877a6222282587b145adaba69afd2d9
unzip -l source
# G97_A_CADIST_P.{cpg,dbf,prj,shp,shx}
python -c 'import geopandas as g; x=g.read_file("G97_A_CADIST_P.shp"); print(x.crs, x.shape, x.geometry.geom_type.value_counts().to_dict(), bool(x.geometry.is_valid.all()))'
# EPSG:3826, (12, 19), {'Polygon': 12}, True
```

The archive response was HTTP 200 with `Content-Type: application/zip` and filename `臺北市區界圖_20220915.zip`. The `.prj` identifies TWD97 Transverse Mercator with central meridian 121 and the file reader resolves it as EPSG:3826. The inspection found 12 records, unique CPID values, non-empty valid Polygon geometries, and the named district fields recorded below.

## Limitations and uncertainty

- FACT: the retrieved resource is published by Taipei City Government Department of Civil Affairs and has the properties above.
- INFERENCE: it is a suitable import candidate for an administrative reference layer.
- UNVERIFIED: legal currency after the resource's 2022-09-15 version, datum realization/precision beyond the EPSG label, topology semantics, and detailed attribute definitions.
- The geometry is administrative reference data. It MUST NOT be represented as rodent observation, infrastructure observation, inferred connectivity, or simulated movement.
- The import MUST retain the source URL, retrieval timestamp, archive hash, resource/version label, license, source CRS, target CRS, and processing notes.
