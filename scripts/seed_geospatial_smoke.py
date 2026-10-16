"""Seed one deterministic, explicitly synthetic administrative fixture for live smoke tests.

This fixture is test data only and is never presented as the official Taipei archive.
It uses the production batch validation, provenance, and persistence functions.
"""

import os

import geopandas as gpd
from ratsight_api.importers.administrative_districts import (
    _build_batch,
    build_provenance,
    persist_import,
)
from ratsight_api.infrastructure.database.connection import SessionLocal
from ratsight_api.infrastructure.database.models import AdministrativeDistrict
from shapely.geometry import box
from sqlalchemy import delete

# A small valid TWD97/EPSG:3826 fixture envelope around Taipei, transformed by _build_batch.
SOURCE_GEOMETRY = box(300000, 2761000, 301000, 2762000)
DATASET_ID = "smoke-fixture"
ARCHIVE_SHA256 = "f" * 64


def main() -> None:
    frame = gpd.GeoDataFrame(
        {"CPID": ["smoke-1"], "TNAME": ["測試行政區"], "geometry": [SOURCE_GEOMETRY]},
        crs="EPSG:3826",
    )
    batch = _build_batch(
        frame,
        dataset_id=DATASET_ID,
        resource_version="test",
        archive_sha256=ARCHIVE_SHA256,
    )
    provenance = build_provenance(
        batch,
        source_url="https://example.invalid/geospatial-smoke-fixture",
        retrieved_at="2026-01-01T00:00:00Z",
        license_text="test fixture only",
        attribution="RatSight automated test fixture",
    )
    with SessionLocal() as session, session.begin():
        session.execute(
            delete(AdministrativeDistrict).where(AdministrativeDistrict.dataset_id == DATASET_ID)
        )
        if os.environ.get("SMOKE_EMPTY") != "1":
            persist_import(session, batch, provenance)
    state = "cleared" if os.environ.get("SMOKE_EMPTY") == "1" else "seeded"
    print(f"{state} synthetic geospatial smoke fixture")


if __name__ == "__main__":
    main()
