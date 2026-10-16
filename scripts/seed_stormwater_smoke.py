"""Seed a deterministic synthetic stormwater fixture through production importer functions."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from ratsight_api.importers.stormwater_pipelines import (
    build_provenance,
    load_and_validate_source,
    persist_import,
)
from ratsight_api.infrastructure.database.connection import SessionLocal
from ratsight_api.infrastructure.database.models import StormwaterPipeline
from sqlalchemy import delete

XML = """<?xml version="1.0" encoding="UTF-8"?>
<UTL xmlns:gml="http://www.opengis.net/gml" xmlns="https://standards.moi.gov.tw/schema/utilityex">
  <UTL_管線>
    <geometry><gml:LineString srsName="EPSG:3826" srsDimension="3">
      <gml:posList>301000 2765000 4 301100 2765100 4</gml:posList>
    </gml:LineString></geometry>
    <識別碼>smoke-segment-1</識別碼><管線編號>SMOKE-1</管線編號>
    <類別碼>8040201</類別碼><起點編號>NODE-A</起點編號><終點編號>NODE-B</終點編號>
    <管線長度>141</管線長度><資料狀態>test</資料狀態>
  </UTL_管線>
</UTL>"""
DATASET_ID = "00000000-0000-4000-8000-000000000001"
RESOURCE_ID = "00000000-0000-4000-8000-000000000002"
RESOURCE_VERSION = "2026-01-01T00:00:00Z"


def main() -> None:
    with TemporaryDirectory() as directory:
        source = Path(directory) / "stormwater.xml"
        source.write_text(XML, encoding="utf-8")
        import hashlib

        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        batch = load_and_validate_source(
            source,
            expected_sha256=digest,
            dataset_id=DATASET_ID,
            resource_id=RESOURCE_ID,
            resource_version=RESOURCE_VERSION,
        )
        provenance = build_provenance(
            batch,
            source_url="https://example.invalid/stormwater-smoke",
            download_url="https://example.invalid/stormwater-smoke.xml",
            retrieved_at="2026-01-01T00:00:00Z",
            license_text="test fixture only",
            attribution="RatSight automated test fixture",
        )
        with SessionLocal() as session, session.begin():
            session.execute(
                delete(StormwaterPipeline).where(StormwaterPipeline.dataset_id == DATASET_ID)
            )
            if os.environ.get("SMOKE_EMPTY") != "1":
                persist_import(session, batch, provenance)
    print(
        "cleared" if os.environ.get("SMOKE_EMPTY") == "1" else "seeded",
        "synthetic stormwater fixture",
    )


if __name__ == "__main__":
    main()
