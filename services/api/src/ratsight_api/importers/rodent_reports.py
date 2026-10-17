"""Fixture-only importer for synthetic rodent report points.

The only permitted input is the committed synthetic fixture
``services/api/tests/fixtures/rodent_reports/synthetic_reports.csv`` with pinned
dataset/version/content hash. It has no source override and never downloads real
citizen reports. Records are SIMULATED report events, not observations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ratsight_api.api.schemas import (
    RodentReportProcessing,
    RodentReportProvenanceV1,
    RodentReportUncertainty,
)
from ratsight_api.domain.rodent_reports import (
    ACTION_STATUSES,
    CSV_COLUMNS,
    FIXTURE_ATTRIBUTION,
    FIXTURE_DATASET_ID,
    FIXTURE_NOTICE,
    FIXTURE_RESOURCE_VERSION,
    FIXTURE_RETRIEVED_AT,
    FIXTURE_SHA256,
    LAT_MAX,
    LAT_MIN,
    LOCATION_PRECISIONS,
    LON_MAX,
    LON_MIN,
    MUNICIPAL_STATUSES,
    REPORT_TYPES,
    REVIEW_STATUSES,
    RODENT_REPORT_CLASSIFICATION,
    RODENT_REPORT_DATA_CLASS,
    SOURCE_KIND,
    UNCERTAINTY_CURRENTNESS,
    UNCERTAINTY_NOTE,
)
from ratsight_api.infrastructure.database.connection import SessionLocal
from ratsight_api.infrastructure.database.models import RodentReport

IMPORTER_TOOL = "ratsight_api.importers.rodent_reports"
IMPORTER_VERSION = "1"
FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "fixtures"
    / "rodent_reports"
    / "synthetic_reports.csv"
)


class RodentReportImportError(ValueError):
    """Raised when the fixture or a record fails validation."""


class RodentReportConflictError(RuntimeError):
    """Raised when an import conflicts with persisted fixture identity."""


@dataclass(frozen=True)
class ReportRecord:
    source_record_id: str
    report_type: str
    reported_at: datetime
    longitude: float
    latitude: float
    location_precision: str
    review_status: str
    municipal_status: str
    action_status: str
    content_sha256: str


@dataclass(frozen=True)
class ImportBatch:
    dataset_id: str
    resource_version: str
    content_sha256: str
    retrieved_at: str
    records: tuple[ReportRecord, ...]


@dataclass(frozen=True)
class ImportReport:
    dataset_id: str
    resource_version: str
    inserted: int
    unchanged: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "resource_version": self.resource_version,
            "inserted": self.inserted,
            "unchanged": self.unchanged,
        }


def compute_file_sha256(source_path: Path) -> str:
    digest = hashlib.sha256()
    with source_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        text = value.decode("utf-8")
    else:
        text = str(value)
    if isinstance(value, float) and math.isnan(value):
        return ""
    return unicodedata.normalize("NFC", text).strip()


def parse_rfc3339_utc(value: str) -> datetime:
    text = value.strip()
    if not text:
        raise ValueError("timestamp is empty")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("timestamp is not RFC3339") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed.astimezone(UTC)


def normalize_rfc3339_utc(value: str) -> str:
    return parse_rfc3339_utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def _enum_value(value: str, allowed: frozenset[str], field: str) -> str:
    normalized = normalize_text(value)
    if normalized not in allowed:
        raise RodentReportImportError(f"{field} has disallowed or empty value: {value!r}")
    return normalized


def _coordinate(value: str, *, minimum: float, maximum: float, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RodentReportImportError(f"{field} is not a number: {value!r}") from exc
    if not math.isfinite(number) or not (minimum <= number <= maximum):
        raise RodentReportImportError(f"{field} is out of EPSG:4326 range: {value!r}")
    return number


def _record_content_hash(
    source_record_id: str,
    report_type: str,
    reported_at: datetime,
    longitude: float,
    latitude: float,
    location_precision: str,
    review_status: str,
    municipal_status: str,
    action_status: str,
) -> str:
    digest = hashlib.sha256()
    for part in (
        source_record_id,
        report_type,
        reported_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        repr(longitude),
        repr(latitude),
        location_precision,
        review_status,
        municipal_status,
        action_status,
    ):
        digest.update(part.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def _parse_records(source_path: Path) -> list[ReportRecord]:
    with source_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise RodentReportImportError("fixture CSV is empty") from exc
        if tuple(header) != CSV_COLUMNS:
            raise RodentReportImportError(
                f"fixture CSV header must be exactly {CSV_COLUMNS}; found {tuple(header)}"
            )
        records: list[ReportRecord] = []
        seen: set[str] = set()
        for line_number, row in enumerate(reader, start=2):
            if len(row) != len(CSV_COLUMNS):
                raise RodentReportImportError(
                    f"row {line_number} has {len(row)} fields; expected {len(CSV_COLUMNS)}"
                )
            values = dict(zip(CSV_COLUMNS, row, strict=True))
            source_record_id = normalize_text(values["source_record_id"])
            if not source_record_id:
                raise RodentReportImportError(f"row {line_number} has an empty source_record_id")
            if source_record_id in seen:
                raise RodentReportImportError(
                    f"duplicate source_record_id at row {line_number}: {source_record_id}"
                )
            seen.add(source_record_id)
            try:
                reported_at = parse_rfc3339_utc(values["reported_at"])
            except ValueError as exc:
                raise RodentReportImportError(
                    f"row {line_number} reported_at is invalid: {exc}"
                ) from exc
            report_type = _enum_value(values["report_type"], REPORT_TYPES, "report_type")
            longitude = _coordinate(
                values["longitude"], minimum=LON_MIN, maximum=LON_MAX, field="longitude"
            )
            latitude = _coordinate(
                values["latitude"], minimum=LAT_MIN, maximum=LAT_MAX, field="latitude"
            )
            location_precision = _enum_value(
                values["location_precision"], LOCATION_PRECISIONS, "location_precision"
            )
            review_status = _enum_value(values["review_status"], REVIEW_STATUSES, "review_status")
            municipal_status = _enum_value(
                values["municipal_status"], MUNICIPAL_STATUSES, "municipal_status"
            )
            action_status = _enum_value(values["action_status"], ACTION_STATUSES, "action_status")
            records.append(
                ReportRecord(
                    source_record_id=source_record_id,
                    report_type=report_type,
                    reported_at=reported_at,
                    longitude=longitude,
                    latitude=latitude,
                    location_precision=location_precision,
                    review_status=review_status,
                    municipal_status=municipal_status,
                    action_status=action_status,
                    content_sha256=_record_content_hash(
                        source_record_id,
                        report_type,
                        reported_at,
                        longitude,
                        latitude,
                        location_precision,
                        review_status,
                        municipal_status,
                        action_status,
                    ),
                )
            )
    if not records:
        raise RodentReportImportError("fixture CSV contains no records")
    return records


def load_and_validate_source(
    source_path: Path,
    *,
    expected_sha256: str,
    dataset_id: str,
    resource_version: str,
    retrieved_at: str = FIXTURE_RETRIEVED_AT,
) -> ImportBatch:
    """Verify fixture identity/hash and validate every record before any write."""
    if not source_path.is_file():
        raise RodentReportImportError(f"fixture not found: {source_path}")
    actual_sha256 = compute_file_sha256(source_path)
    if actual_sha256 != expected_sha256:
        raise RodentReportImportError(
            f"fixture SHA-256 mismatch: expected {expected_sha256}, computed {actual_sha256}"
        )
    return ImportBatch(
        dataset_id=dataset_id,
        resource_version=resource_version,
        content_sha256=actual_sha256,
        retrieved_at=retrieved_at,
        records=tuple(_parse_records(source_path)),
    )


def build_provenance(batch: ImportBatch) -> RodentReportProvenanceV1:
    return RodentReportProvenanceV1(
        schema_version="1",
        source_kind=SOURCE_KIND,
        dataset_id=batch.dataset_id,
        resource_version=batch.resource_version,
        retrieved_at=batch.retrieved_at,
        content_sha256=batch.content_sha256,
        license=FIXTURE_NOTICE,
        attribution=FIXTURE_ATTRIBUTION,
        source_crs="EPSG:4326",
        target_crs="EPSG:4326",
        processing=RodentReportProcessing(
            tool=IMPORTER_TOOL,
            tool_version=IMPORTER_VERSION,
            steps=[
                f"validated committed synthetic fixture header and {len(batch.records)} rows",
                f"verified pinned dataset/version/content hash {batch.content_sha256}",
                "rejected unknown/forbidden columns and invalid coordinates/times/enums",
            ],
        ),
        synthetic=True,
        uncertainty=RodentReportUncertainty(
            currentness=UNCERTAINTY_CURRENTNESS,
            note=UNCERTAINTY_NOTE,
        ),
    )


def persist_import(
    session: Session,
    batch: ImportBatch,
    provenance: RodentReportProvenanceV1,
) -> ImportReport:
    """Transactionally insert one fixture version; caller owns the transaction."""
    existing_rows = session.execute(
        select(RodentReport.source_record_id, RodentReport.content_sha256)
        .where(RodentReport.dataset_id == batch.dataset_id)
        .where(RodentReport.resource_version == batch.resource_version)
    ).all()
    existing = {row.source_record_id: row.content_sha256 for row in existing_rows}
    incoming = {record.source_record_id: record for record in batch.records}
    if existing:
        if set(existing) != set(incoming):
            raise RodentReportConflictError(
                "fixture record identity set changed; "
                "content for an existing version must be identical"
            )
        changed = [
            record.source_record_id
            for record in batch.records
            if existing[record.source_record_id] != record.content_sha256
        ]
        if changed:
            raise RodentReportConflictError(
                f"fixture content changed for an existing version: {sorted(changed)}"
            )

    provenance_payload = provenance.model_dump(mode="json")
    inserted = 0
    for record in batch.records:
        if record.source_record_id in existing:
            continue
        session.execute(
            pg_insert(RodentReport).values(
                source_record_id=record.source_record_id,
                dataset_id=batch.dataset_id,
                resource_version=batch.resource_version,
                content_sha256=record.content_sha256,
                data_class=RODENT_REPORT_DATA_CLASS,
                classification=RODENT_REPORT_CLASSIFICATION,
                report_type=record.report_type,
                reported_at=record.reported_at,
                location_precision=record.location_precision,
                review_status=record.review_status,
                municipal_status=record.municipal_status,
                action_status=record.action_status,
                provenance=provenance_payload,
                geometry=from_shape(Point(record.longitude, record.latitude), srid=4326),
            )
        )
        inserted += 1
    session.flush()
    return ImportReport(
        dataset_id=batch.dataset_id,
        resource_version=batch.resource_version,
        inserted=inserted,
        unchanged=len(existing),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m ratsight_api.importers.rodent_reports",
        description=(
            "Import the committed synthetic rodent-report fixture. Fixture-only; "
            "no real source download or source override."
        ),
    )
    parser.add_argument("--inspect-only", action="store_true")
    args = parser.parse_args(argv)

    try:
        batch = load_and_validate_source(
            FIXTURE_PATH,
            expected_sha256=FIXTURE_SHA256,
            dataset_id=FIXTURE_DATASET_ID,
            resource_version=FIXTURE_RESOURCE_VERSION,
        )
    except RodentReportImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    provenance = build_provenance(batch)
    if args.inspect_only:
        print(
            json.dumps(
                {
                    "dataset_id": batch.dataset_id,
                    "resource_version": batch.resource_version,
                    "content_sha256": batch.content_sha256,
                    "record_count": len(batch.records),
                    "provenance": provenance.model_dump(mode="json"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    try:
        with SessionLocal() as session, session.begin():
            report = persist_import(session, batch, provenance)
    except RodentReportConflictError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    except SQLAlchemyError as exc:
        print(f"error: rodent report storage unavailable: {exc}", file=sys.stderr)
        return 4

    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
