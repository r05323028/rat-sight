"""Local-XML importer for the Taipei stormwater infrastructure reference layer.

Candidate B (Evidence ID EVID-TPE-STORMWATER-NETWORK-2026-10-16) is a GML-like
utility XML with homogeneous 3D LineStrings in EPSG:3826. This importer verifies
the file SHA-256 and candidate identity, parses only 3D LineStrings, validates
finite non-empty horizontal geometry, drops the undocumented vertical coordinate,
transforms to 2D EPSG:4326, and transactionally inserts records keyed by the
normalized ``識別碼``.

It does not download data, infer topology/connectivity, or invent identifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import shapely
from defusedxml.ElementTree import iterparse as defused_iterparse
from geoalchemy2.shape import from_shape
from pyproj import Transformer
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ratsight_api.api.schemas import (
    StormwaterProcessing,
    StormwaterProvenanceV1,
    StormwaterSourceQuality,
    StormwaterUncertainty,
)
from ratsight_api.domain.stormwater import (
    OFFICIAL_ARCHIVE_SHA256,
    OFFICIAL_ATTRIBUTION,
    OFFICIAL_DATASET_ID,
    OFFICIAL_DOWNLOAD_URL,
    OFFICIAL_LICENSE,
    OFFICIAL_RESOURCE_ID,
    OFFICIAL_RESOURCE_VERSION,
    OFFICIAL_SOURCE_URL,
    PIPELINE_RECORD_TAG,
    REFERENCE_ONLY_WARNING,
    SOURCE_ATTRIBUTE_MAP,
    SOURCE_CRS,
    SOURCE_RECORD_ID_TAG,
    STORMWATER_CLASSIFICATION,
    STORMWATER_DATA_CLASS,
    TARGET_CRS,
)
from ratsight_api.infrastructure.database.connection import SessionLocal
from ratsight_api.infrastructure.database.models import StormwaterPipeline

IMPORTER_TOOL = "ratsight_api.importers.stormwater_pipelines"
IMPORTER_VERSION = "1"
REQUIRED_LINE_DIMENSION = 3
_ATTRIBUTE_TAGS = {tag for _, tag in SOURCE_ATTRIBUTE_MAP}


class StormwaterImportError(ValueError):
    """Raised when the source file fails identity, CRS, or geometry validation."""


class StormwaterConflictError(RuntimeError):
    """Raised when an import conflicts with persisted stormwater identity."""


@dataclass(frozen=True)
class PipelineRecord:
    source_record_id: str
    attributes: dict[str, str]
    geometry: Any
    content_hash: str


@dataclass(frozen=True)
class ImportBatch:
    dataset_id: str
    resource_id: str
    resource_version: str
    archive_sha256: str
    records: tuple[PipelineRecord, ...]
    source_quality: dict[str, Any]
    z_handling: Literal["dropped", "retained", "not_present"]


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
    """Decode UTF-8 where needed and return a trimmed Unicode NFC string."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        text = value.decode("utf-8")
    else:
        text = str(value)
    if isinstance(value, float) and math.isnan(value):
        return ""
    return unicodedata.normalize("NFC", text).strip()


def _local_name(tag: Any) -> str:
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    if ":" in tag:
        return tag.rsplit(":", 1)[1]
    return tag


def _record_attributes(element: Any) -> dict[str, str]:
    raw: dict[str, str] = {}
    for child in element:
        name = _local_name(child.tag)
        if name in _ATTRIBUTE_TAGS:
            raw[name] = normalize_text(child.text)
    return {public_name: raw.get(tag, "") for public_name, tag in SOURCE_ATTRIBUTE_MAP}


def _first_descendant(element: Any, name: str) -> Any | None:
    for child in element.iter():
        if _local_name(child.tag) == name:
            return child
    return None


def _parse_positions(line_element: Any) -> list[tuple[float, float, float]]:
    srs_name = (line_element.get("srsName") or "").strip().upper()
    if srs_name != "EPSG:3826":
        raise StormwaterImportError(
            f"LineString must declare EPSG:3826 exactly, found {srs_name!r}"
        )

    dimension_attribute = line_element.get("srsDimension")
    if dimension_attribute is None or dimension_attribute.strip() != str(REQUIRED_LINE_DIMENSION):
        raise StormwaterImportError(
            "LineString srsDimension must be declared as homogeneous 3D (3), "
            f"found {dimension_attribute!r}"
        )

    pos_list = _first_descendant(line_element, "posList")
    if pos_list is None or not pos_list.text:
        raise StormwaterImportError("LineString has no posList")
    raw_values = pos_list.text.split()
    try:
        numbers = [float(value) for value in raw_values]
    except ValueError as exc:
        raise StormwaterImportError("LineString posList contains non-numeric values") from exc
    if any(not math.isfinite(number) for number in numbers):
        raise StormwaterImportError("LineString contains non-finite coordinates")
    if len(numbers) % REQUIRED_LINE_DIMENSION != 0:
        raise StormwaterImportError("mixed LineString dimensions are not supported")
    positions = [
        (numbers[index], numbers[index + 1], numbers[index + 2])
        for index in range(0, len(numbers), REQUIRED_LINE_DIMENSION)
    ]
    return positions


def _to_epsg_4326(positions: list[tuple[float, float, float]]) -> Any:
    xy = [(x, y) for x, y, _ in positions]
    if len(xy) < 2:
        raise StormwaterImportError("LineString requires at least two positions")
    if len(set(xy)) < 2:
        raise StormwaterImportError("LineString has fewer than two distinct positions")
    source_line = shapely.LineString(xy)
    if source_line.is_empty or not source_line.is_valid:
        raise StormwaterImportError("LineString horizontal geometry is invalid")
    transformer = Transformer.from_crs(SOURCE_CRS, TARGET_CRS, always_xy=True)
    xs, ys = transformer.transform([x for x, _ in xy], [y for _, y in xy])
    coordinates = [
        (float(x), float(y))
        for x, y in zip(xs, ys, strict=True)
        if math.isfinite(x) and math.isfinite(y)
    ]
    if len(coordinates) != len(xy):
        raise StormwaterImportError("transformed LineString contains non-finite coordinates")
    if len(set(coordinates)) < 2:
        raise StormwaterImportError("transformed LineString has fewer than two distinct positions")
    target_line = shapely.LineString(coordinates)
    if target_line.is_empty or not target_line.is_valid:
        raise StormwaterImportError("transformed LineString geometry is invalid")
    return target_line


def _content_hash(source_record_id: str, attributes: dict[str, str], geometry: Any) -> str:
    digest = hashlib.sha256()
    digest.update(source_record_id.encode("utf-8"))
    digest.update(b"\x00")
    for name in sorted(attributes):
        digest.update(name.encode("utf-8"))
        digest.update(b"\x01")
        digest.update(attributes[name].encode("utf-8"))
        digest.update(b"\x00")
    digest.update(shapely.to_wkb(geometry))
    return digest.hexdigest()


def _parse_pipeline_record(element: Any) -> PipelineRecord:
    source_record_id = normalize_text(_first_text(element, SOURCE_RECORD_ID_TAG))
    if not source_record_id:
        raise StormwaterImportError(f"record is missing a non-empty {SOURCE_RECORD_ID_TAG}")

    attributes = _record_attributes(element)
    line_element = _first_descendant(element, "LineString")
    if line_element is None:
        raise StormwaterImportError("record has no GML LineString")
    geometry = _to_epsg_4326(_parse_positions(line_element))
    return PipelineRecord(
        source_record_id=source_record_id,
        attributes={name: value for name, value in attributes.items() if value},
        geometry=geometry,
        content_hash=_content_hash(source_record_id, attributes, geometry),
    )


def _first_text(element: Any, name: str) -> str:
    for child in element:
        if _local_name(child.tag) == name:
            return child.text or ""
    return ""


def _parse_records(source_path: Path) -> list[PipelineRecord]:
    records: list[PipelineRecord] = []
    seen: set[str] = set()
    try:
        for _, element in defused_iterparse(source_path, events=("end",)):
            if _local_name(element.tag) != PIPELINE_RECORD_TAG:
                continue
            record = _parse_pipeline_record(element)
            if record.source_record_id in seen:
                raise StormwaterImportError(
                    f"duplicate {SOURCE_RECORD_ID_TAG} value: {record.source_record_id}"
                )
            seen.add(record.source_record_id)
            records.append(record)
            element.clear()
    except StormwaterImportError:
        raise
    except Exception as exc:  # noqa: BLE001 - defusedxml raises several parse errors
        raise StormwaterImportError("source XML could not be parsed securely") from exc
    if not records:
        raise StormwaterImportError(f"source contains no {PIPELINE_RECORD_TAG} records")
    return records


def _source_quality(records: list[PipelineRecord]) -> dict[str, int]:
    pipe_numbers = [record.attributes.get("pipe_number", "") for record in records]
    non_empty = [value for value in pipe_numbers if value]
    counts: dict[str, int] = {}
    for value in non_empty:
        counts[value] = counts.get(value, 0) + 1
    return {
        "missing_pipe_number_count": sum(1 for value in pipe_numbers if not value),
        "duplicate_pipe_number_value_count": sum(1 for count in counts.values() if count > 1),
        "missing_start_endpoint_count": sum(
            1 for record in records if not record.attributes.get("start_node_id")
        ),
        "missing_end_endpoint_count": sum(
            1 for record in records if not record.attributes.get("end_node_id")
        ),
        "missing_notes_count": sum(1 for record in records if not record.attributes.get("notes")),
    }


def load_and_validate_source(
    source_path: Path,
    *,
    expected_sha256: str,
    dataset_id: str,
    resource_id: str,
    resource_version: str,
) -> ImportBatch:
    """Verify the source file hash/identity and validate every pipeline record."""
    if not source_path.is_file():
        raise StormwaterImportError(f"source file not found: {source_path}")
    actual_sha256 = compute_file_sha256(source_path)
    if actual_sha256 != expected_sha256.lower():
        raise StormwaterImportError(
            f"source SHA-256 mismatch: expected {expected_sha256.lower()}, computed {actual_sha256}"
        )
    records = tuple(_parse_records(source_path))
    return ImportBatch(
        dataset_id=dataset_id,
        resource_id=resource_id,
        resource_version=resource_version,
        archive_sha256=actual_sha256,
        records=records,
        source_quality=_source_quality(list(records)),
        z_handling="dropped",
    )


def build_provenance(
    batch: ImportBatch,
    *,
    source_url: str,
    download_url: str,
    retrieved_at: str,
    license_text: str,
    attribution: str,
) -> StormwaterProvenanceV1:
    return StormwaterProvenanceV1(
        schema_version="1",
        source_url=source_url,
        download_url=download_url,
        dataset_id=batch.dataset_id,
        resource_id=batch.resource_id,
        resource_version=batch.resource_version,
        retrieved_at=retrieved_at,
        archive_sha256=batch.archive_sha256,
        license=license_text,
        attribution=attribution,
        source_crs=SOURCE_CRS,
        target_crs=TARGET_CRS,
        z_handling=batch.z_handling,
        processing=StormwaterProcessing(
            tool=IMPORTER_TOOL,
            tool_version=IMPORTER_VERSION,
            steps=[
                f"verified source SHA-256 {batch.archive_sha256}",
                f"validated {len(batch.records)} homogeneous 3D EPSG:3826 LineStrings",
                "dropped unverified third coordinate; output 2D EPSG:4326",
                f"recorded source-quality counts {batch.source_quality}",
            ],
        ),
        source_quality=StormwaterSourceQuality(
            reference_only=True,
            missing_pipe_number_count=batch.source_quality["missing_pipe_number_count"],
            duplicate_pipe_number_value_count=batch.source_quality[
                "duplicate_pipe_number_value_count"
            ],
            missing_start_endpoint_count=batch.source_quality["missing_start_endpoint_count"],
            missing_end_endpoint_count=batch.source_quality["missing_end_endpoint_count"],
            missing_notes_count=batch.source_quality["missing_notes_count"],
        ),
        uncertainty=StormwaterUncertainty(
            currentness=(
                f"resource version {batch.resource_version}; legal/engineering currency "
                "and completeness are unverified"
            ),
            note=(
                f"{REFERENCE_ONLY_WARNING}; not verified physical connectivity, "
                "traversability, or rodent evidence"
            ),
        ),
    )


def persist_import(
    session: Session,
    batch: ImportBatch,
    provenance: StormwaterProvenanceV1,
) -> ImportReport:
    """Transactionally insert one source version; caller owns the transaction."""
    existing_rows = session.execute(
        select(
            StormwaterPipeline.source_record_id,
            StormwaterPipeline.archive_sha256,
            StormwaterPipeline.content_hash,
        )
        .where(StormwaterPipeline.dataset_id == batch.dataset_id)
        .where(StormwaterPipeline.resource_version == batch.resource_version)
    ).all()
    existing = {row.source_record_id: row for row in existing_rows}
    incoming = {record.source_record_id: record for record in batch.records}
    if existing:
        if {row.archive_sha256 for row in existing.values()} != {batch.archive_sha256}:
            raise StormwaterConflictError(
                "existing source version was imported with a different archive hash; "
                "use a new resource version"
            )
        if set(existing) != set(incoming):
            missing = sorted(set(existing) - set(incoming))
            added = sorted(set(incoming) - set(existing))
            raise StormwaterConflictError(
                f"source record identity set changed (missing={missing}, added={added}); "
                "content for an existing source version must be identical"
            )
        changed = [
            record.source_record_id
            for record in batch.records
            if existing[record.source_record_id].content_hash != record.content_hash
        ]
        if changed:
            raise StormwaterConflictError(
                f"source content changed for an existing version: {sorted(changed)}"
            )

    provenance_payload = provenance.model_dump(mode="json")
    inserted = 0
    for record in batch.records:
        if record.source_record_id in existing:
            continue
        values: dict[str, Any] = {
            "source_record_id": record.source_record_id,
            "dataset_id": batch.dataset_id,
            "resource_id": batch.resource_id,
            "resource_version": batch.resource_version,
            "archive_sha256": batch.archive_sha256,
            "data_class": STORMWATER_DATA_CLASS,
            "classification": STORMWATER_CLASSIFICATION,
            "content_hash": record.content_hash,
            "provenance": provenance_payload,
            "geometry": from_shape(record.geometry, srid=4326),
        }
        for name in record.attributes:
            values[name] = record.attributes[name]
        session.execute(pg_insert(StormwaterPipeline).values(**values))
        inserted += 1
    session.flush()
    return ImportReport(
        dataset_id=batch.dataset_id,
        resource_version=batch.resource_version,
        inserted=inserted,
        unchanged=len(existing),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ratsight_api.importers.stormwater_pipelines",
        description=(
            "Import the documented Taipei stormwater utility XML into PostGIS. "
            "Local file only; no live download."
        ),
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--dataset-id", default=OFFICIAL_DATASET_ID)
    parser.add_argument("--resource-id", default=OFFICIAL_RESOURCE_ID)
    parser.add_argument("--resource-version", default=OFFICIAL_RESOURCE_VERSION)
    parser.add_argument("--source-url", default=OFFICIAL_SOURCE_URL)
    parser.add_argument("--download-url", default=OFFICIAL_DOWNLOAD_URL)
    parser.add_argument("--license", default=OFFICIAL_LICENSE, dest="license_text")
    parser.add_argument("--attribution", default=OFFICIAL_ATTRIBUTION)
    parser.add_argument("--inspect-only", action="store_true")
    parser.add_argument(
        "--allow-nonofficial-source",
        action="store_true",
        help="Allow deterministic test fixtures with non-official identity/hash values.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.allow_nonofficial_source and (
        args.dataset_id != OFFICIAL_DATASET_ID
        or args.resource_id != OFFICIAL_RESOURCE_ID
        or args.resource_version != OFFICIAL_RESOURCE_VERSION
        or args.archive_sha256.lower() != OFFICIAL_ARCHIVE_SHA256
    ):
        print(
            "error: official importer identity is pinned; use --allow-nonofficial-source only "
            "for deterministic tests",
            file=sys.stderr,
        )
        return 2
    try:
        batch = load_and_validate_source(
            args.source,
            expected_sha256=args.archive_sha256,
            dataset_id=args.dataset_id,
            resource_id=args.resource_id,
            resource_version=args.resource_version,
        )
    except StormwaterImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        provenance = build_provenance(
            batch,
            source_url=args.source_url,
            download_url=args.download_url,
            retrieved_at=args.retrieved_at,
            license_text=args.license_text,
            attribution=args.attribution,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.inspect_only:
        print(
            json.dumps(
                {
                    "dataset_id": batch.dataset_id,
                    "resource_id": batch.resource_id,
                    "resource_version": batch.resource_version,
                    "archive_sha256": batch.archive_sha256,
                    "record_count": len(batch.records),
                    "source_quality": batch.source_quality,
                    "z_handling": batch.z_handling,
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
    except StormwaterConflictError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    except SQLAlchemyError as exc:
        print(f"error: stormwater storage unavailable: {exc}", file=sys.stderr)
        return 4

    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
