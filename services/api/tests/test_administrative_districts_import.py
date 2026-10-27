"""Importer and model tests for administrative reference district boundaries.

Validation tests are database-free. Persistence tests are gated on a reachable
PostGIS instance and never drop or reset shared tables.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, cast

import geopandas as gpd
import pytest
from geoalchemy2 import Geometry
from ratsight_api.domain.administrative_districts import (
    ADMINISTRATIVE_DATA_CLASS,
    DISTRICT_CLASSIFICATION,
)
from ratsight_api.importers.administrative_districts import (
    ImportValidationError,
    compute_archive_sha256,
    load_and_validate_archive,
    normalize_text,
)
from ratsight_api.infrastructure.database.connection import SessionLocal, engine
from ratsight_api.infrastructure.database.models import AdministrativeDistrict
from shapely.geometry import Point, Polygon
from sqlalchemy import CheckConstraint, Table, UniqueConstraint, inspect, text
from sqlalchemy.exc import SQLAlchemyError

DATASET_ID = "121199"
RESOURCE_VERSION = "20220915"
TEST_DATASET_ID = "ratsight-test-administrative-districts"
TEST_RESOURCE_VERSION = "test-20220915"
SHAPEFILE_BASE = "G97_A_CADIST_P"


def _valid_polygons() -> list[Polygon]:
    return [
        Polygon([(121.50, 25.00), (121.52, 25.00), (121.52, 25.02), (121.50, 25.02)]),
        Polygon([(121.53, 25.00), (121.55, 25.00), (121.55, 25.02), (121.53, 25.02)]),
    ]


def _write_shapefile(
    tmp_path: Path,
    *,
    crs: str,
    identifiers: tuple[str, ...],
    names: tuple[str, ...],
    geometries: list[Any] | None = None,
    override_crs: str | None = None,
) -> Path:
    frame = gpd.GeoDataFrame(
        {"CPID": list(identifiers), "TNAME": list(names)},
        geometry=list(geometries) if geometries is not None else _valid_polygons(),
        crs="EPSG:4326",
    )
    if override_crs is not None:
        frame = frame.set_crs(override_crs, allow_override=True)
    elif crs != "EPSG:4326":
        frame = frame.to_crs(crs)
    shp_path = tmp_path / f"{SHAPEFILE_BASE}.shp"
    frame.to_file(shp_path, driver="ESRI Shapefile")
    return shp_path


def _make_archive(
    tmp_path: Path,
    *,
    crs: str = "EPSG:3826",
    identifiers: tuple[str, ...] = ("A", "B"),
    names: tuple[str, ...] = ("中正區", "大安區"),
    geometries: list[Any] | None = None,
    override_crs: str | None = None,
    drop_suffixes: tuple[str, ...] = (),
) -> tuple[Path, str]:
    shp_path = _write_shapefile(
        tmp_path,
        crs=crs,
        identifiers=identifiers,
        names=names,
        geometries=geometries,
        override_crs=override_crs,
    )
    archive_path = tmp_path / "districts.zip"
    components = [
        shp_path.with_suffix(suffix) for suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg")
    ]
    with zipfile.ZipFile(archive_path, "w") as archive:
        for component in components:
            if component.suffix in drop_suffixes or not component.exists():
                continue
            archive.write(component, arcname=component.name)
    return archive_path, compute_archive_sha256(archive_path)


def _load(archive: Path, sha256: str, **overrides: str):
    arguments = {
        "expected_sha256": sha256,
        "dataset_id": DATASET_ID,
        "resource_version": RESOURCE_VERSION,
    }
    arguments.update(overrides)
    return load_and_validate_archive(archive, **arguments)


def test_valid_archive_is_normalized_and_within_envelopes(tmp_path: Path) -> None:
    archive, sha256 = _make_archive(tmp_path)
    batch = _load(archive, sha256)
    assert {record.district_id for record in batch.records} == {"A", "B"}
    assert [record.district_name for record in batch.records] == ["中正區", "大安區"]
    assert all(record.geometry.geom_type in {"Polygon", "MultiPolygon"} for record in batch.records)
    assert all(record.content_hash for record in batch.records)
    assert batch.archive_sha256 == sha256


def test_archive_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    archive, _ = _make_archive(tmp_path)
    wrong = "0" * 64
    with pytest.raises(ImportValidationError, match="SHA-256 mismatch"):
        _load(archive, wrong)


def test_missing_prj_is_rejected(tmp_path: Path) -> None:
    archive, sha256 = _make_archive(tmp_path, drop_suffixes=(".prj",))
    with pytest.raises(ImportValidationError, match="missing required shapefile components"):
        _load(archive, sha256)


def test_unsupported_source_crs_is_rejected(tmp_path: Path) -> None:
    archive, sha256 = _make_archive(tmp_path, crs="EPSG:4326")
    with pytest.raises(ImportValidationError, match="source CRS must be EPSG:3826"):
        _load(archive, sha256)


def test_axis_swapped_coordinates_are_rejected(tmp_path: Path) -> None:
    archive, sha256 = _make_archive(tmp_path, override_crs="EPSG:3826")
    with pytest.raises(ImportValidationError, match="outside the EPSG:3826 envelope"):
        _load(archive, sha256)


def test_out_of_envelope_coordinates_are_rejected(tmp_path: Path) -> None:
    far = [
        Polygon([(120.0, 23.0), (120.02, 23.0), (120.02, 23.02), (120.0, 23.02)]),
        Polygon([(120.03, 23.0), (120.05, 23.0), (120.05, 23.02), (120.03, 23.02)]),
    ]
    archive, sha256 = _make_archive(tmp_path, geometries=far)
    with pytest.raises(ImportValidationError, match="outside the EPSG:3826 envelope"):
        _load(archive, sha256)


def test_unsupported_geometry_type_is_rejected(tmp_path: Path) -> None:
    points = [Point(121.50, 25.00), Point(121.53, 25.00)]
    archive, sha256 = _make_archive(tmp_path, geometries=points)
    with pytest.raises(ImportValidationError, match="unsupported geometry type"):
        _load(archive, sha256)


def test_invalid_geometry_is_rejected_without_repair(tmp_path: Path) -> None:
    bowtie = Polygon([(121.50, 25.00), (121.52, 25.02), (121.52, 25.00), (121.50, 25.02)])
    squares = _valid_polygons()
    archive, sha256 = _make_archive(tmp_path, geometries=[bowtie, squares[1]])
    with pytest.raises(ImportValidationError, match="invalid geometry is not allowed"):
        _load(archive, sha256)


def test_duplicate_identifier_is_rejected(tmp_path: Path) -> None:
    archive, sha256 = _make_archive(tmp_path, identifiers=("A", "A"))
    with pytest.raises(ImportValidationError, match="duplicate identifiers"):
        _load(archive, sha256)


def test_empty_name_is_rejected(tmp_path: Path) -> None:
    archive, sha256 = _make_archive(tmp_path, names=("中正區", "   "))
    with pytest.raises(ImportValidationError, match="empty name"):
        _load(archive, sha256)


def test_missing_required_attribute_is_rejected(tmp_path: Path) -> None:
    shp_path = _write_shapefile(tmp_path, crs="EPSG:3826", identifiers=("A", "B"), names=("a", "b"))
    frame = gpd.read_file(shp_path).drop(columns=["TNAME"])
    frame.to_file(shp_path, driver="ESRI Shapefile")
    archive_path = tmp_path / "districts.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
            component = shp_path.with_suffix(suffix)
            if component.exists():
                archive.write(component, arcname=component.name)
    with pytest.raises(ImportValidationError, match="missing required attribute"):
        _load(archive_path, compute_archive_sha256(archive_path))


def test_unsafe_archive_member_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../evil.shp", b"x")
    with pytest.raises(ImportValidationError, match="unsafe member paths"):
        _load(archive_path, compute_archive_sha256(archive_path))


def test_normalize_text_decodes_and_applies_nfc() -> None:
    decomposed = "  \u4e2d\u6b63\u5340  "
    assert normalize_text(decomposed) == "\u4e2d\u6b63\u5340"
    assert normalize_text("大安區".encode()) == "大安區"
    assert normalize_text(None) == ""
    assert normalize_text(float("nan")) == ""


def test_model_defines_expected_columns_and_constraints() -> None:
    table = cast(Table, AdministrativeDistrict.__table__)
    assert set(table.columns.keys()) >= {
        "district_id",
        "district_name",
        "dataset_id",
        "resource_version",
        "archive_sha256",
        "data_class",
        "classification",
        "provenance",
        "content_hash",
        "geometry",
    }
    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns}
        == {"dataset_id", "resource_version", "district_id"}
    ]
    assert unique_constraints, "expected the (dataset, version, district) unique key"
    check_sql = " ".join(
        str(constraint.sqltext)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    )
    assert "ADMINISTRATIVE_REFERENCE" in check_sql
    assert "GeometryType" in check_sql
    assert cast(Geometry, table.c.geometry.type).srid == 4326


def _postgis_available() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT PostGIS_Version()"))
        return True
    except SQLAlchemyError:
        return False


def _table_exists() -> bool:
    try:
        return inspect(engine).has_table("administrative_districts")
    except SQLAlchemyError:
        return False


@pytest.mark.skipif(not _postgis_available(), reason="PostGIS unavailable")
@pytest.mark.skipif(not _table_exists(), reason="administrative_districts migration not applied")
def test_persist_import_is_transactional_and_idempotent(tmp_path: Path) -> None:
    from ratsight_api.importers.administrative_districts import build_provenance, persist_import

    archive, sha256 = _make_archive(tmp_path)
    batch = _load(
        archive,
        sha256,
        dataset_id=TEST_DATASET_ID,
        resource_version=TEST_RESOURCE_VERSION,
    )
    provenance = build_provenance(
        batch,
        source_url="https://example.test/resource",
        retrieved_at="2026-10-15T00:00:00Z",
        license_text="Open Government Data License v1",
        attribution="Taipei City Government Department of Civil Affairs",
    )
    with SessionLocal() as session:
        try:
            first = persist_import(session, batch, provenance)
            session.flush()
            assert first.inserted == 2
            second = persist_import(session, batch, provenance)
            session.flush()
            assert second.unchanged == 2
            count = session.execute(
                text(
                    "SELECT count(*) FROM administrative_districts "
                    "WHERE dataset_id = :d AND resource_version = :v"
                ),
                {"d": TEST_DATASET_ID, "v": TEST_RESOURCE_VERSION},
            ).scalar_one()
            assert count == 2
            stored = session.execute(
                text(
                    "SELECT DISTINCT data_class, classification FROM administrative_districts "
                    "WHERE dataset_id = :d"
                ),
                {"d": TEST_DATASET_ID},
            ).all()
            assert {tuple(row) for row in stored} == {
                (ADMINISTRATIVE_DATA_CLASS, DISTRICT_CLASSIFICATION)
            }
        finally:
            session.rollback()
