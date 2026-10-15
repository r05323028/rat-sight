"""Archive-only importer for administrative reference district boundaries.

The importer is deliberately narrow: it accepts one source archive, verifies its
hash, validates a non-ambiguous EPSG:3826 shapefile with finite valid
Polygon/MultiPolygon geometry inside documented envelopes, and transactionally
upserts districts keyed by ``(dataset_id, resource_version, district_id)``.

It does not download data, repair invalid geometry, or infer district counts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import shapely
from geoalchemy2.shape import from_shape
from pyproj import CRS
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ratsight_api.api.schemas import (
    ProvenanceProcessing,
    ProvenanceUncertainty,
    ProvenanceV1,
)
from ratsight_api.domain.administrative_districts import (
    ADMINISTRATIVE_DATA_CLASS,
    DISTRICT_CLASSIFICATION,
    DISTRICT_ID_ATTRIBUTE,
    DISTRICT_NAME_ATTRIBUTE,
    PROVENANCE_SCHEMA_VERSION,
    SOURCE_CRS,
    SOURCE_ENVELOPE,
    TARGET_CRS,
    TARGET_ENVELOPE,
)
from ratsight_api.infrastructure.database.connection import SessionLocal
from ratsight_api.infrastructure.database.models import AdministrativeDistrict

IMPORTER_TOOL = "ratsight_api.importers.administrative_districts"
IMPORTER_VERSION = "1"
REQUIRED_SUFFIXES = (".shp", ".shx", ".dbf", ".prj")
REQUIRED_ATTRIBUTES = (DISTRICT_ID_ATTRIBUTE, DISTRICT_NAME_ATTRIBUTE)
GEOMETRY_TYPES = {"Polygon", "MultiPolygon"}


class ImportValidationError(ValueError):
    """Raised when the source archive or its contents fail validation."""


class ImportConflictError(RuntimeError):
    """Raised when an import conflicts with already-persisted source identity."""


@dataclass(frozen=True)
class DistrictRecord:
    district_id: str
    district_name: str
    geometry: Any
    content_hash: str


@dataclass(frozen=True)
class ImportBatch:
    dataset_id: str
    resource_version: str
    archive_sha256: str
    records: tuple[DistrictRecord, ...]
    source_bounds: tuple[float, float, float, float]
    target_bounds: tuple[float, float, float, float]
    geometry_types: dict[str, int]


@dataclass(frozen=True)
class ImportReport:
    dataset_id: str
    resource_version: str
    inserted: int
    updated: int
    unchanged: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "resource_version": self.resource_version,
            "inserted": self.inserted,
            "updated": self.updated,
            "unchanged": self.unchanged,
        }


def compute_archive_sha256(archive_path: Path) -> str:
    digest = hashlib.sha256()
    with archive_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(value: Any) -> str:
    """Decode UTF-8 where needed and return a trimmed Unicode NFC string.

    Missing values (``None``/NaN, as shapefile drivers emit for blank fields)
    normalize to an empty string so callers reject them explicitly.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    if isinstance(value, bytes):
        decoded = value.decode("utf-8")
    else:
        decoded = str(value)
    return unicodedata.normalize("NFC", decoded).strip()


def _unsafe_members(names: list[str]) -> list[str]:
    unsafe: list[str] = []
    for name in names:
        candidate = Path(name)
        if candidate.is_absolute() or ".." in candidate.parts:
            unsafe.append(name)
    return unsafe


def _locate_shapefile(names: list[str]) -> str:
    shapefiles = [name for name in names if name.lower().endswith(".shp")]
    if len(shapefiles) != 1:
        raise ImportValidationError(f"expected exactly one .shp member, found {len(shapefiles)}")
    lowered = {name.lower() for name in names}
    base = shapefiles[0][:-4]
    missing = [suffix for suffix in REQUIRED_SUFFIXES if (base + suffix).lower() not in lowered]
    if missing:
        raise ImportValidationError(f"archive missing required shapefile components: {missing}")
    return shapefiles[0]


def _validate_source_crs(frame: gpd.GeoDataFrame) -> None:
    if frame.crs is None:
        raise ImportValidationError("source has no declared CRS (.prj missing or unreadable)")
    try:
        source = CRS.from_user_input(frame.crs)
    except Exception as exc:  # noqa: BLE001 - pyproj raises several error types
        raise ImportValidationError("source CRS is not a parseable CRS") from exc
    if not source.equals(CRS.from_epsg(3826)):
        raise ImportValidationError(f"source CRS must be EPSG:3826, found {frame.crs!r}")


def _validate_geometries(geometries: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for geometry in geometries:
        if geometry is None:
            raise ImportValidationError("geometry is missing")
        geometry_type = geometry.geom_type
        if geometry_type not in GEOMETRY_TYPES:
            raise ImportValidationError(f"unsupported geometry type: {geometry_type}")
        if geometry.has_z or geometry.has_m:
            raise ImportValidationError("Z/M geometry dimensions are not supported")
        if geometry.is_empty:
            raise ImportValidationError("empty geometry is not allowed")
        if not geometry.is_valid:
            raise ImportValidationError("invalid geometry is not allowed; repair is not silent")
        counts[geometry_type] = counts.get(geometry_type, 0) + 1
    return counts


def _coordinate_bounds(geometries: Any) -> tuple[float, float, float, float]:
    coordinates = np.asarray(shapely.get_coordinates(geometries), dtype=float)
    if coordinates.size == 0:
        raise ImportValidationError("geometry contains no coordinates")
    if not np.isfinite(coordinates).all():
        raise ImportValidationError("non-finite coordinates are not allowed")
    return (
        float(coordinates[:, 0].min()),
        float(coordinates[:, 1].min()),
        float(coordinates[:, 0].max()),
        float(coordinates[:, 1].max()),
    )


def _within_envelope(
    bounds: tuple[float, float, float, float],
    envelope: tuple[float, float, float, float],
) -> bool:
    min_x, min_y, max_x, max_y = bounds
    env_min_x, env_min_y, env_max_x, env_max_y = envelope
    return env_min_x <= min_x and env_min_y <= min_y and max_x <= env_max_x and max_y <= env_max_y


def content_hash(district_id: str, district_name: str, geometry: Any) -> str:
    digest = hashlib.sha256()
    digest.update(district_id.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(district_name.encode("utf-8"))
    digest.update(b"\x00")
    digest.update(shapely.to_wkb(geometry))
    return digest.hexdigest()


def _build_batch(
    frame: gpd.GeoDataFrame,
    *,
    dataset_id: str,
    resource_version: str,
    archive_sha256: str,
) -> ImportBatch:
    if frame.empty:
        raise ImportValidationError("source contains no records")
    _validate_source_crs(frame)
    for attribute in REQUIRED_ATTRIBUTES:
        if attribute not in frame.columns:
            raise ImportValidationError(f"source is missing required attribute: {attribute}")

    source_types = _validate_geometries(frame.geometry)
    source_bounds = _coordinate_bounds(frame.geometry.values)
    if not _within_envelope(source_bounds, SOURCE_ENVELOPE):
        raise ImportValidationError(
            f"source coordinates {source_bounds} fall outside the EPSG:3826 envelope "
            f"{SOURCE_ENVELOPE}"
        )

    district_ids = [normalize_text(value) for value in frame[DISTRICT_ID_ATTRIBUTE]]
    district_names = [normalize_text(value) for value in frame[DISTRICT_NAME_ATTRIBUTE]]
    if any(not value for value in district_ids):
        raise ImportValidationError(f"{DISTRICT_ID_ATTRIBUTE} contains an empty identifier")
    if len(set(district_ids)) != len(district_ids):
        raise ImportValidationError(f"{DISTRICT_ID_ATTRIBUTE} contains duplicate identifiers")
    if any(not value for value in district_names):
        raise ImportValidationError(f"{DISTRICT_NAME_ATTRIBUTE} contains an empty name")

    transformed = frame.to_crs(TARGET_CRS)
    target_types = _validate_geometries(transformed.geometry)
    target_bounds = _coordinate_bounds(transformed.geometry.values)
    if not _within_envelope(target_bounds, TARGET_ENVELOPE):
        raise ImportValidationError(
            f"transformed coordinates {target_bounds} fall outside the EPSG:4326 envelope "
            f"{TARGET_ENVELOPE}"
        )

    records = tuple(
        DistrictRecord(
            district_id=district_id,
            district_name=district_name,
            geometry=geometry,
            content_hash=content_hash(district_id, district_name, geometry),
        )
        for district_id, district_name, geometry in zip(
            district_ids, district_names, transformed.geometry, strict=True
        )
    )
    return ImportBatch(
        dataset_id=dataset_id,
        resource_version=resource_version,
        archive_sha256=archive_sha256,
        records=records,
        source_bounds=source_bounds,
        target_bounds=target_bounds,
        geometry_types={**source_types, **target_types},
    )


def load_and_validate_archive(
    archive_path: Path,
    *,
    expected_sha256: str,
    dataset_id: str,
    resource_version: str,
) -> ImportBatch:
    """Verify the archive hash and validate its single EPSG:3826 shapefile."""
    if not archive_path.is_file():
        raise ImportValidationError(f"archive not found: {archive_path}")
    actual_sha256 = compute_archive_sha256(archive_path)
    if actual_sha256 != expected_sha256.lower():
        raise ImportValidationError(
            "archive SHA-256 mismatch: "
            f"expected {expected_sha256.lower()}, computed {actual_sha256}"
        )

    with zipfile.ZipFile(archive_path) as archive:
        members = [name for name in archive.namelist() if not name.endswith("/")]
        unsafe = _unsafe_members(members)
        if unsafe:
            raise ImportValidationError(f"archive contains unsafe member paths: {unsafe}")
        shapefile = _locate_shapefile(members)
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive.extractall(path=temporary_directory, members=members)
            frame = gpd.read_file(Path(temporary_directory) / shapefile)
            return _build_batch(
                frame,
                dataset_id=dataset_id,
                resource_version=resource_version,
                archive_sha256=actual_sha256,
            )


def build_provenance(
    batch: ImportBatch,
    *,
    source_url: str,
    retrieved_at: str,
    license_text: str,
    attribution: str,
) -> ProvenanceV1:
    return ProvenanceV1(
        schema_version=PROVENANCE_SCHEMA_VERSION,
        source_url=source_url,
        dataset_id=batch.dataset_id,
        resource_version=batch.resource_version,
        retrieved_at=retrieved_at,
        archive_sha256=batch.archive_sha256,
        license=license_text,
        attribution=attribution,
        source_crs=SOURCE_CRS,
        target_crs=TARGET_CRS,
        processing=ProvenanceProcessing(
            tool=IMPORTER_TOOL,
            tool_version=IMPORTER_VERSION,
            steps=[
                f"verified archive SHA-256 {batch.archive_sha256}",
                f"validated EPSG:3826 source envelope {batch.source_bounds}",
                f"validated {len(batch.records)} Polygon/MultiPolygon records",
                f"transformed to EPSG:4326 within envelope {batch.target_bounds}",
                "normalized CPID/TNAME with Unicode NFC and trimmed whitespace",
            ],
        ),
        uncertainty=ProvenanceUncertainty(
            currentness=(
                f"resource version {batch.resource_version}; legal currency after this "
                "version is unresolved"
            ),
            note=(
                "administrative reference geometry only; not rodent observation, "
                "infrastructure, inferred connectivity, or simulated movement"
            ),
        ),
    )


def persist_import(
    session: Session,
    batch: ImportBatch,
    provenance: ProvenanceV1,
) -> ImportReport:
    """Transactionally upsert one source version; caller owns the transaction."""
    existing_rows = session.execute(
        select(
            AdministrativeDistrict.district_id,
            AdministrativeDistrict.archive_sha256,
            AdministrativeDistrict.content_hash,
        )
        .where(AdministrativeDistrict.dataset_id == batch.dataset_id)
        .where(AdministrativeDistrict.resource_version == batch.resource_version)
    ).all()
    existing = {row.district_id: row for row in existing_rows}
    if existing:
        existing_hashes = {row.archive_sha256 for row in existing.values()}
        if existing_hashes != {batch.archive_sha256}:
            raise ImportConflictError(
                f"dataset {batch.dataset_id} version {batch.resource_version} already imported "
                "with a different archive hash; use a new resource version"
            )
        omitted = sorted(set(existing) - {record.district_id for record in batch.records})
        if omitted:
            raise ImportConflictError(
                f"import omits previously imported district identifiers {omitted}; "
                "deletion is not implicit"
            )

    provenance_payload = provenance.model_dump(mode="json")
    inserted = updated = unchanged = 0
    for record in batch.records:
        prior = existing.get(record.district_id)
        if prior is not None and prior.content_hash == record.content_hash:
            unchanged += 1
            continue
        statement = pg_insert(AdministrativeDistrict).values(
            district_id=record.district_id,
            district_name=record.district_name,
            dataset_id=batch.dataset_id,
            resource_version=batch.resource_version,
            archive_sha256=batch.archive_sha256,
            data_class=ADMINISTRATIVE_DATA_CLASS,
            classification=DISTRICT_CLASSIFICATION,
            provenance=provenance_payload,
            content_hash=record.content_hash,
            geometry=from_shape(record.geometry, srid=4326),
        )
        session.execute(
            statement.on_conflict_do_update(
                constraint="uq_administrative_districts_key",
                set_={
                    "district_name": record.district_name,
                    "archive_sha256": batch.archive_sha256,
                    "data_class": ADMINISTRATIVE_DATA_CLASS,
                    "classification": DISTRICT_CLASSIFICATION,
                    "provenance": provenance_payload,
                    "content_hash": record.content_hash,
                    "geometry": from_shape(record.geometry, srid=4326),
                    "updated_at": func.now(),
                },
            )
        )
        if prior is None:
            inserted += 1
        else:
            updated += 1
    session.flush()
    return ImportReport(
        dataset_id=batch.dataset_id,
        resource_version=batch.resource_version,
        inserted=inserted,
        updated=updated,
        unchanged=unchanged,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ratsight_api.importers.administrative_districts",
        description=(
            "Import the documented Taipei administrative district boundary archive into "
            "PostGIS. Archive-only; no live download."
        ),
    )
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--resource-version", required=True)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--license", required=True, dest="license_text")
    parser.add_argument("--attribution", required=True)
    parser.add_argument(
        "--inspect-only",
        action="store_true",
        help="Validate the archive without writing to PostGIS.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        batch = load_and_validate_archive(
            args.archive,
            expected_sha256=args.archive_sha256,
            dataset_id=args.dataset_id,
            resource_version=args.resource_version,
        )
    except ImportValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    provenance = build_provenance(
        batch,
        source_url=args.source_url,
        retrieved_at=args.retrieved_at,
        license_text=args.license_text,
        attribution=args.attribution,
    )
    if args.inspect_only:
        print(
            json.dumps(
                {
                    "dataset_id": batch.dataset_id,
                    "resource_version": batch.resource_version,
                    "archive_sha256": batch.archive_sha256,
                    "district_count": len(batch.records),
                    "geometry_types": batch.geometry_types,
                    "source_bounds": batch.source_bounds,
                    "target_bounds": batch.target_bounds,
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
    except ImportConflictError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    except SQLAlchemyError as exc:
        print(f"error: administrative district storage unavailable: {exc}", file=sys.stderr)
        return 4

    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())
