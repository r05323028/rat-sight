"""Seed or verify the committed synthetic rodent-report fixture for smoke tests.

The ``rodent_reports`` table is immutable after import: migration 0004 installs a
database trigger that blocks UPDATE and DELETE. This script therefore never
deletes rows. ``SMOKE_EMPTY=1`` only verifies that the disposable smoke database
is freshly empty; the smoke harness must recreate its disposable volume to reset.

It never downloads or reads a real report source.
"""

from __future__ import annotations

import os
import sys

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
from sqlalchemy import func, select

EXIT_NOT_EMPTY = 3


def fixture_row_count() -> int:
    with SessionLocal() as session:
        return session.execute(
            select(func.count())
            .select_from(RodentReport)
            .where(RodentReport.dataset_id == FIXTURE_DATASET_ID)
        ).scalar_one()


def main() -> int:
    if os.environ.get("SMOKE_EMPTY") == "1":
        count = fixture_row_count()
        if count:
            print(
                "error: SMOKE_EMPTY requires a freshly recreated disposable database; "
                f"{count} fixture rows already exist. rodent_reports is immutable, so the "
                "smoke harness must recreate the disposable volume instead of deleting rows.",
                file=sys.stderr,
            )
            return EXIT_NOT_EMPTY
        print("verified empty synthetic rodent report fixture")
        return 0

    batch = load_and_validate_source(
        FIXTURE_PATH,
        expected_sha256=FIXTURE_SHA256,
        dataset_id=FIXTURE_DATASET_ID,
        resource_version=FIXTURE_RESOURCE_VERSION,
    )
    provenance = build_provenance(batch)
    with SessionLocal() as session, session.begin():
        persist_import(session, batch, provenance)
    print("seeded synthetic rodent report fixture")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
