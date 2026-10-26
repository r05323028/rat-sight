"""Aggregate a public citizen-report export into suppressed 250 m grid counts.

Input is a locally held export of a public citizen-report platform (Rat Radar,
``ratdar.taipei``). The importer never stores per-report rows: it reads
coordinates, wall-clock month, and report type, then writes only cell/month/
type counts for cells that reach the suppression minimum. Free text, place
names, photo URLs, and exact report points are dropped before any write.

Aggregates stay ``UNVERIFIED`` citizen reports. They are not observations,
prevalence, population, movement, or disease-risk evidence, and they are never
a simulation input.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from geoalchemy2.shape import from_shape
from shapely.geometry import box
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import CursorResult, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ratsight_api.api.schemas import (
    CitizenReportAggregation,
    CitizenReportCounts,
    CitizenReportProcessing,
    CitizenReportProvenanceV1,
    CitizenReportUncertainty,
)
from ratsight_api.domain.citizen_report_aggregates import (
    ATTRIBUTION,
    CELL_SIZE_METERS,
    CITIZEN_REPORT_CLASSIFICATION,
    CITIZEN_REPORT_DATA_CLASS,
    DATASET_ID,
    DEFAULT_REPORT_TYPE,
    DROPPED_COLUMNS,
    LICENSE_NOTE,
    MONTH_TIMEZONE_ASSUMPTION,
    NOTICE,
    RAW_COLUMNS,
    REPORT_TYPE_CODES,
    SOURCE_KIND,
    SOURCE_URL,
    SUPPRESSION_MINIMUM,
)
from ratsight_api.infrastructure.database.connection import SessionLocal
from ratsight_api.infrastructure.database.models import CitizenReportCell

IMPORTER_TOOL = "ratsight_api.importers.citizen_report_aggregates"
IMPORTER_VERSION = "1"
LAT_STEP = CELL_SIZE_METERS / 111_320.0


class CitizenReportImportError(ValueError):
    """Raised when the export fails validation before any write."""


@dataclass(frozen=True)
class AggregateRow:
    cell_id: str
    month: str
    report_type: str
    count: int
    south: float
    west: float
    north: float
    east: float

    @property
    def record_id(self) -> str:
        return f"{self.cell_id}:{self.month}:{self.report_type}"


@dataclass(frozen=True)
class AggregateBatch:
    dataset_id: str
    resource_version: str
    retrieved_at: str
    content_sha256: str
    rows: tuple[AggregateRow, ...]
    parsed: int
    used: int
    invalid_coordinates: int
    suppressed_records: int
    suppressed_cells: int


def compute_file_sha256(source_path: Path) -> str:
    digest = hashlib.sha256()
    with source_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cell(latitude: float, longitude: float) -> tuple[str, float, float, float, float]:
    lat_index = math.floor(latitude / LAT_STEP)
    center_lat = (lat_index + 0.5) * LAT_STEP
    lon_step = LAT_STEP / max(math.cos(math.radians(center_lat)), 1e-6)
    lon_index = math.floor(longitude / lon_step)
    south = lat_index * LAT_STEP
    west = lon_index * lon_step
    return (
        f"g{CELL_SIZE_METERS}m:{lat_index}:{lon_index}",
        south,
        west,
        south + LAT_STEP,
        west + lon_step,
    )


def _month(value: str) -> str:
    text = value.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return parsed.strftime("%Y-%m")
    raise CitizenReportImportError(f"通報時間 is not a parseable timestamp: {value!r}")


def _coordinate(value: str, *, limit: float, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise CitizenReportImportError(f"{field} is not a number: {value!r}") from exc
    if not math.isfinite(number) or not -limit <= number <= limit:
        raise CitizenReportImportError(f"{field} is out of range: {value!r}")
    return number


def aggregate_export(source_path: Path) -> AggregateBatch:
    """Read the export and return suppressed cell/month/type counts only."""
    if not source_path.is_file():
        raise CitizenReportImportError(f"citizen report export not found: {source_path}")

    counts: dict[tuple[str, str, str], int] = defaultdict(int)
    cell_totals: dict[tuple[str, str], int] = defaultdict(int)
    cell_bounds: dict[str, tuple[float, float, float, float]] = {}
    parsed = 0
    invalid = 0

    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in RAW_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise CitizenReportImportError(f"export is missing required columns: {missing}")
        for row in reader:
            parsed += 1
            try:
                latitude = _coordinate(row["緯度"], limit=90.0, field="緯度")
                longitude = _coordinate(row["經度"], limit=180.0, field="經度")
                month = _month(row["通報時間"])
            except CitizenReportImportError:
                invalid += 1
                continue
            if not (math.isfinite(latitude) and math.isfinite(longitude)):
                invalid += 1
                continue
            report_type = REPORT_TYPE_CODES.get((row["類型"] or "").strip(), DEFAULT_REPORT_TYPE)
            cell_id, south, west, north, east = _cell(latitude, longitude)
            cell_bounds.setdefault(cell_id, (south, west, north, east))
            counts[(cell_id, month, report_type)] += 1
            cell_totals[(cell_id, month)] += 1

    if parsed == 0:
        raise CitizenReportImportError("citizen report export contains no rows")

    suppressed_keys = {key for key, total in cell_totals.items() if total < SUPPRESSION_MINIMUM}
    rows: list[AggregateRow] = []
    suppressed_records = 0
    for (cell_id, month, report_type), count in sorted(counts.items()):
        if (cell_id, month) in suppressed_keys or count < SUPPRESSION_MINIMUM:
            suppressed_records += count
            continue
        south, west, north, east = cell_bounds[cell_id]
        rows.append(
            AggregateRow(
                cell_id=cell_id,
                month=month,
                report_type=report_type,
                count=count,
                south=south,
                west=west,
                north=north,
                east=east,
            )
        )
    if not rows:
        raise CitizenReportImportError("no cell reached the suppression minimum")

    retrieved_at = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%SZ")
    return AggregateBatch(
        dataset_id=DATASET_ID,
        resource_version=retrieved_at,
        retrieved_at=retrieved_at,
        content_sha256=compute_file_sha256(source_path),
        rows=tuple(rows),
        parsed=parsed,
        used=sum(row.count for row in rows),
        invalid_coordinates=invalid,
        suppressed_records=suppressed_records,
        suppressed_cells=len(suppressed_keys),
    )


PROCESSING_STEPS = (
    "只讀取通報時間/類型/緯度/經度；地點、說明、照片網址在聚合前即丟棄",
    f"將 EPSG:4326 座標投影到 {CELL_SIZE_METERS} 公尺網格並指派 cell_id",
    "以通報時間的本月桶（亞洲台北牆鐘時間，UTC 位移未驗證）分月",
    f"抑制少於 {SUPPRESSION_MINIMUM} 筆的網格-月份群組與個別類型列，不寫入任何個別通報",
)


def build_provenance(batch: AggregateBatch) -> CitizenReportProvenanceV1:
    return CitizenReportProvenanceV1(
        source_kind=SOURCE_KIND,
        dataset_id=batch.dataset_id,
        resource_version=batch.resource_version,
        retrieved_at=batch.retrieved_at,
        content_sha256=batch.content_sha256,
        source_url=SOURCE_URL,
        license=LICENSE_NOTE,
        attribution=ATTRIBUTION,
        processing=CitizenReportProcessing(
            tool=IMPORTER_TOOL,
            tool_version=IMPORTER_VERSION,
            steps=list(PROCESSING_STEPS),
        ),
        aggregation=CitizenReportAggregation(
            cell_size_meters=CELL_SIZE_METERS,
            month_timezone_assumption=MONTH_TIMEZONE_ASSUMPTION,
            suppression_minimum=SUPPRESSION_MINIMUM,
            dropped_fields=list(DROPPED_COLUMNS),
        ),
        counts=CitizenReportCounts(
            parsed=batch.parsed,
            used=batch.used,
            invalid_coordinates=batch.invalid_coordinates,
            suppressed_records=batch.suppressed_records,
            suppressed_cells=batch.suppressed_cells,
        ),
        uncertainty=CitizenReportUncertainty(currentness=batch.retrieved_at, note=NOTICE),
    )


def _with_reused_version(batch: AggregateBatch, existing: str | None) -> AggregateBatch:
    """Reuse the version already stored for this exact export content."""
    if existing is None or existing == batch.resource_version:
        return batch
    return replace(batch, resource_version=existing)


def _stored_version(session: Session, batch: AggregateBatch) -> str | None:
    try:
        return session.execute(
            select(CitizenReportCell.resource_version)
            .where(CitizenReportCell.dataset_id == batch.dataset_id)
            .where(CitizenReportCell.content_sha256 == batch.content_sha256)
            .limit(1)
        ).scalar_one_or_none()
    except SQLAlchemyError as exc:
        session.rollback()
        raise CitizenReportImportError(
            f"could not read existing citizen report aggregates: {exc}"
        ) from exc


def persist_batch(session: Session, batch: AggregateBatch) -> dict[str, int]:
    """Write suppressed rows idempotently; per-report input is never stored."""
    batch = _with_reused_version(batch, _stored_version(session, batch))
    provenance = build_provenance(batch).model_dump(mode="json")
    payload = [
        {
            "dataset_id": batch.dataset_id,
            "resource_version": batch.resource_version,
            "content_sha256": batch.content_sha256,
            "data_class": CITIZEN_REPORT_DATA_CLASS,
            "classification": CITIZEN_REPORT_CLASSIFICATION,
            "cell_id": row.cell_id,
            "month": row.month,
            "report_type": row.report_type,
            "report_count": row.count,
            "provenance": provenance,
            "geometry": from_shape(
                box(row.west, row.south, row.east, row.north),
                srid=4326,
            ),
        }
        for row in batch.rows
    ]
    inserted = 0
    try:
        for start in range(0, len(payload), 500):
            statement = (
                pg_insert(CitizenReportCell)
                .values(payload[start : start + 500])
                .on_conflict_do_nothing(constraint="uq_citizen_report_cells_key")
            )
            cursor = cast("CursorResult[Any]", session.execute(statement))
            inserted += max(cursor.rowcount or 0, 0)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise CitizenReportImportError(
            f"could not persist citizen report aggregates: {exc}"
        ) from exc
    return {
        "rows": len(payload),
        "inserted": inserted,
        "unchanged": len(payload) - inserted,
        "resource_version": batch.resource_version,
    }


def _summary(batch: AggregateBatch, persisted: dict[str, int] | None = None) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "dataset_id": batch.dataset_id,
        "resource_version": batch.resource_version,
        "content_sha256": batch.content_sha256,
        "rows": len(batch.rows),
        "parsed_records": batch.parsed,
        "used_records": batch.used,
        "invalid_coordinates": batch.invalid_coordinates,
        "suppressed_records": batch.suppressed_records,
        "suppressed_cells": batch.suppressed_cells,
    }
    if persisted is not None:
        summary["persistence"] = persisted
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate a public citizen-report export into suppressed 250 m cells. "
            "Only counts are written; free text, place names, photo URLs, and exact "
            "report points never leave the source file."
        )
    )
    parser.add_argument("--source", required=True, help="path to the local CSV export")
    parser.add_argument(
        "--inspect-only",
        action="store_true",
        help="validate and summarize the export without writing to the database",
    )
    args = parser.parse_args(argv)

    batch = aggregate_export(Path(args.source))
    if args.inspect_only:
        print(json.dumps(_summary(batch), ensure_ascii=False, indent=2))
        return 0

    with SessionLocal() as session:
        persisted = persist_batch(session, batch)
    print(json.dumps(_summary(batch, persisted), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
