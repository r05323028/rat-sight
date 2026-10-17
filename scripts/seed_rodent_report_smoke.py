"""Seed or clear the committed synthetic rodent-report fixture for live smoke tests.

This uses the production fixture validation, provenance, and persistence
functions. It never downloads or reads a real report source.
"""

import os

from ratsight_api.importers.rodent_reports import (
    FIXTURE_DATASET_ID,
    FIXTURE_PATH,
    FIXTURE_RESOURCE_VERSION,
    FIXTURE_SHA256,
    build_provenance,
    load_and_validate_source,
    persist_import,
)
from ratsight_api.infrastructure.database.connection import SessionLocal
from ratsight_api.infrastructure.database.models import RodentReport
from sqlalchemy import delete


def main() -> None:
    batch = load_and_validate_source(
        FIXTURE_PATH,
        expected_sha256=FIXTURE_SHA256,
        dataset_id=FIXTURE_DATASET_ID,
        resource_version=FIXTURE_RESOURCE_VERSION,
    )
    provenance = build_provenance(batch)
    with SessionLocal() as session, session.begin():
        session.execute(delete(RodentReport).where(RodentReport.dataset_id == FIXTURE_DATASET_ID))
        if os.environ.get("SMOKE_EMPTY") != "1":
            persist_import(session, batch, provenance)
    state = "cleared" if os.environ.get("SMOKE_EMPTY") == "1" else "seeded"
    print(f"{state} synthetic rodent report fixture")


if __name__ == "__main__":
    main()
