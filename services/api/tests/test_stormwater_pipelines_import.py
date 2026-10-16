"""Importer and model tests for stormwater infrastructure reference pipelines.

Validation tests are database-free. Persistence tests are gated on a reachable
PostGIS instance and never drop or reset shared tables.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from ratsight_api.domain.stormwater import (
    OFFICIAL_DATASET_ID,
    OFFICIAL_RESOURCE_ID,
    OFFICIAL_RESOURCE_VERSION,
    STORMWATER_CLASSIFICATION,
    STORMWATER_DATA_CLASS,
)
from ratsight_api.importers.stormwater_pipelines import (
    StormwaterConflictError,
    StormwaterImportError,
    build_provenance,
    compute_file_sha256,
    load_and_validate_source,
    normalize_text,
)
from ratsight_api.infrastructure.database.connection import SessionLocal, engine
from ratsight_api.infrastructure.database.models import StormwaterPipeline
from sqlalchemy import CheckConstraint, Table, UniqueConstraint, inspect, text
from sqlalchemy.exc import SQLAlchemyError

GML_NS = "http://www.opengis.net/gml"


def _record_xml(
    record_id: str,
    *,
    pipe_number: str = "PN1",
    start_node: str = "S1",
    end_node: str = "E1",
    notes: str = "note",
    srs_name: str = "EPSG:3826",
    dimension: int | None = 3,
    positions: tuple[tuple[float, ...], ...] = (
        (300000.0, 2765000.0, 10.0),
        (300100.0, 2765100.0, 11.0),
    ),
) -> str:
    attributes = {
        "類別碼": "SW",
        "識別碼": record_id,
        "起點編號": start_node,
        "終點編號": end_node,
        "管線編號": pipe_number,
        "管線材料": "RCP",
        "備註": notes,
    }
    attribute_xml = "".join(f"<{key}>{value}</{key}>" for key, value in attributes.items())
    position_text = " ".join(" ".join(str(value) for value in point) for point in positions)
    dimension_attribute = f' srsDimension="{dimension}"' if dimension is not None else ""
    return (
        "<UTL_管線>"
        f"{attribute_xml}"
        f'<gml:LineString xmlns:gml="{GML_NS}" srsName="{srs_name}"{dimension_attribute}>'
        f"<gml:posList>{position_text}</gml:posList>"
        "</gml:LineString>"
        "</UTL_管線>"
    )


def _write_source(tmp_path: Path, records: list[str]) -> tuple[Path, str]:
    source = tmp_path / "stormwater.xml"
    source.write_text(
        '<?xml version="1.0" encoding="UTF-8"?><UTL>' + "".join(records) + "</UTL>",
        encoding="utf-8",
    )
    return source, compute_file_sha256(source)


def _load(source: Path, sha256: str, **overrides: str):
    arguments = {
        "expected_sha256": sha256,
        "dataset_id": OFFICIAL_DATASET_ID,
        "resource_id": OFFICIAL_RESOURCE_ID,
        "resource_version": OFFICIAL_RESOURCE_VERSION,
    }
    arguments.update(overrides)
    return load_and_validate_source(source, **arguments)


def test_valid_source_parses_2d_lines_and_quality(tmp_path: Path) -> None:
    source, sha256 = _write_source(
        tmp_path,
        [
            _record_xml("P001", pipe_number="PN1"),
            _record_xml("P002", pipe_number="PN1", start_node="", end_node="", notes=""),
        ],
    )
    batch = _load(source, sha256)
    assert [record.source_record_id for record in batch.records] == ["P001", "P002"]
    assert batch.records[0].geometry.geom_type == "LineString"
    assert batch.records[0].geometry.has_z is False
    assert batch.records[0].attributes["material"] == "RCP"
    assert "notes" not in batch.records[1].attributes
    assert batch.source_quality == {
        "missing_pipe_number_count": 0,
        "duplicate_pipe_number_value_count": 1,
        "missing_start_endpoint_count": 1,
        "missing_end_endpoint_count": 1,
        "missing_notes_count": 1,
    }
    assert batch.z_handling == "dropped"


def test_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    source, _ = _write_source(tmp_path, [_record_xml("P001")])
    with pytest.raises(StormwaterImportError, match="SHA-256 mismatch"):
        _load(source, "0" * 64)


def test_missing_srs_name_is_rejected(tmp_path: Path) -> None:
    source, sha256 = _write_source(tmp_path, [_record_xml("P001", srs_name="")])
    with pytest.raises(StormwaterImportError, match="EPSG:3826"):
        _load(source, sha256)


def test_near_match_srs_name_is_rejected(tmp_path: Path) -> None:
    source, sha256 = _write_source(tmp_path, [_record_xml("P001", srs_name="EPSG:13826")])
    with pytest.raises(StormwaterImportError, match="exactly"):
        _load(source, sha256)


def test_2d_dimension_is_rejected(tmp_path: Path) -> None:
    source, sha256 = _write_source(
        tmp_path,
        [
            _record_xml(
                "P001", dimension=2, positions=((300000.0, 2765000.0), (300100.0, 2765100.0))
            )
        ],
    )
    with pytest.raises(StormwaterImportError, match="srsDimension"):
        _load(source, sha256)


def test_non_homogeneous_coordinate_count_is_rejected(tmp_path: Path) -> None:
    source, sha256 = _write_source(
        tmp_path, [_record_xml("P001", dimension=None, positions=((300000.0, 2765000.0),))]
    )
    with pytest.raises(StormwaterImportError, match="homogeneous 3D"):
        _load(source, sha256)


def test_missing_source_record_id_is_rejected(tmp_path: Path) -> None:
    source, sha256 = _write_source(tmp_path, [_record_xml("")])
    with pytest.raises(StormwaterImportError, match="識別碼"):
        _load(source, sha256)


def test_duplicate_source_record_id_is_rejected(tmp_path: Path) -> None:
    source, sha256 = _write_source(tmp_path, [_record_xml("P001"), _record_xml("P001")])
    with pytest.raises(StormwaterImportError, match="duplicate"):
        _load(source, sha256)


def test_degenerate_line_is_rejected(tmp_path: Path) -> None:
    source, sha256 = _write_source(
        tmp_path,
        [
            _record_xml(
                "P001",
                positions=((300000.0, 2765000.0, 10.0), (300000.0, 2765000.0, 10.0)),
            )
        ],
    )
    with pytest.raises(StormwaterImportError, match="distinct"):
        _load(source, sha256)


def test_empty_source_is_rejected(tmp_path: Path) -> None:
    source, sha256 = _write_source(tmp_path, [])
    with pytest.raises(StormwaterImportError, match="no UTL_管線 records"):
        _load(source, sha256)


def test_normalize_text_applies_nfc_and_treats_nan_as_empty() -> None:
    assert normalize_text("  \u7ba1\u7dda  ") == "\u7ba1\u7dda"
    assert normalize_text(None) == ""
    assert normalize_text(float("nan")) == ""


def test_build_provenance_matches_typed_contract(tmp_path: Path) -> None:
    source, sha256 = _write_source(tmp_path, [_record_xml("P001")])
    batch = _load(source, sha256)
    provenance = build_provenance(
        batch,
        source_url="https://example.test/source",
        download_url="https://example.test/download",
        retrieved_at="2026-10-16T00:00:00Z",
        license_text="Open Government Data License v1",
        attribution="Taipei City Government Public Works Department",
    )
    assert provenance.z_handling == "dropped"
    assert provenance.source_quality.reference_only is True
    assert provenance.source_crs == "EPSG:3826"
    assert provenance.target_crs == "EPSG:4326"


def test_model_defines_expected_columns_and_constraints() -> None:
    table = cast(Table, StormwaterPipeline.__table__)
    assert set(table.columns.keys()) >= {
        "source_record_id",
        "dataset_id",
        "resource_id",
        "resource_version",
        "archive_sha256",
        "data_class",
        "classification",
        "content_hash",
        "geometry",
        "category_code",
        "pipe_number",
        "start_node_id",
        "end_node_id",
        "notes",
    }
    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns}
        == {"dataset_id", "resource_version", "source_record_id"}
    ]
    assert unique_constraints, "expected the (dataset, version, source_record) unique key"
    check_sql = " ".join(
        str(constraint.sqltext)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    )
    assert "INFRASTRUCTURE_REFERENCE" in check_sql
    assert "LINESTRING" in check_sql
    assert table.c.geometry.type.srid == 4326  # type: ignore[attr-defined]


def _postgis_available() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT PostGIS_Version()"))
        return True
    except SQLAlchemyError:
        return False


def _table_exists() -> bool:
    try:
        return inspect(engine).has_table("stormwater_pipelines")
    except SQLAlchemyError:
        return False


@pytest.mark.skipif(not _postgis_available(), reason="PostGIS unavailable")
@pytest.mark.skipif(not _table_exists(), reason="stormwater_pipelines migration not applied")
def test_persist_import_is_transactional_and_idempotent(tmp_path: Path) -> None:
    from ratsight_api.importers.stormwater_pipelines import persist_import

    source, sha256 = _write_source(
        tmp_path, [_record_xml("P001"), _record_xml("P002", pipe_number="PN1")]
    )
    batch = _load(source, sha256)
    provenance = build_provenance(
        batch,
        source_url="https://example.test/source",
        download_url="https://example.test/download",
        retrieved_at="2026-10-16T00:00:00Z",
        license_text="Open Database License",
        attribution="Taipei City Government Public Works Department",
    )
    with SessionLocal() as session:
        try:
            first = persist_import(session, batch, provenance)
            assert first.inserted == 2
            second = persist_import(session, batch, provenance)
            assert second.unchanged == 2
            row = session.execute(
                text(
                    "SELECT DISTINCT data_class, classification FROM stormwater_pipelines "
                    "WHERE dataset_id = :d"
                ),
                {"d": OFFICIAL_DATASET_ID},
            ).all()
            assert {tuple(item) for item in row} == {
                (STORMWATER_DATA_CLASS, STORMWATER_CLASSIFICATION)
            }
            hash_sha = hashlib.sha256(b"x").hexdigest()
            conflicting_batch = replace(batch, archive_sha256=hash_sha)
            with pytest.raises(StormwaterConflictError, match="different archive hash"):
                persist_import(session, conflicting_batch, provenance)
        finally:
            session.rollback()


@pytest.mark.skipif(not _postgis_available(), reason="PostGIS unavailable")
@pytest.mark.skipif(not _table_exists(), reason="stormwater_pipelines migration not applied")
def test_bbox_filter_selects_only_matching_lines(tmp_path: Path) -> None:
    from ratsight_api.application.stormwater_pipelines import list_stormwater_pipelines
    from ratsight_api.importers.stormwater_pipelines import persist_import

    source, sha256 = _write_source(
        tmp_path,
        [
            _record_xml(
                "P001",
                positions=((300000.0, 2765000.0, 10.0), (300100.0, 2765100.0, 11.0)),
            ),
            _record_xml(
                "P002",
                positions=((315000.0, 2785000.0, 10.0), (315100.0, 2785100.0, 11.0)),
            ),
        ],
    )
    batch = _load(source, sha256)
    provenance = build_provenance(
        batch,
        source_url="https://example.test/source",
        download_url="https://example.test/download",
        retrieved_at="2026-10-16T00:00:00Z",
        license_text="Open Database License",
        attribution="Taipei City Government Public Works Department",
    )
    with SessionLocal() as session:
        try:
            persist_import(session, batch, provenance)
            session.flush()
            min_x, min_y, max_x, max_y = batch.records[0].geometry.bounds
            bbox = (min_x - 0.001, min_y - 0.001, max_x + 0.001, max_y + 0.001)
            response = list_stormwater_pipelines(session, bbox=bbox, dataset_id=OFFICIAL_DATASET_ID)
            assert response.data_state == "available"
            assert response.feature_count == 1
            assert [feature.id for feature in response.features] == ["P001"]
            assert response.bbox == bbox

            miss = list_stormwater_pipelines(
                session, bbox=(121.0, 24.0, 121.05, 24.05), dataset_id=OFFICIAL_DATASET_ID
            )
            assert miss.data_state == "available"
            assert miss.feature_count == 0
            assert miss.provenance is not None
        finally:
            session.rollback()
