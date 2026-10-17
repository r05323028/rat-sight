"""Importer and model tests for fixture-only synthetic rodent reports.

Validation tests are database-free. Persistence tests are gated on PostGIS.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError
from ratsight_api.domain.rodent_reports import (
    CSV_COLUMNS,
    FIXTURE_DATASET_ID,
    FIXTURE_RESOURCE_VERSION,
    FIXTURE_SHA256,
    RODENT_REPORT_CLASSIFICATION,
    RODENT_REPORT_DATA_CLASS,
)
from ratsight_api.importers.rodent_reports import (
    FIXTURE_PATH,
    RodentReportConflictError,
    RodentReportImportError,
    build_provenance,
    compute_file_sha256,
    load_and_validate_source,
)
from ratsight_api.infrastructure.database.connection import SessionLocal, engine
from ratsight_api.infrastructure.database.models import RodentReport
from sqlalchemy import CheckConstraint, Table, UniqueConstraint, inspect, text
from sqlalchemy.exc import SQLAlchemyError

COLUMNS = list(CSV_COLUMNS)


def _row(
    record_id: str = "RR-1",
    *,
    report_type: str = "sighting_report",
    reported_at: str = "2026-10-01T08:15:00Z",
    longitude: str = "121.5265",
    latitude: str = "25.0330",
    location_precision: str = "synthetic_point",
    review_status: str = "unreviewed",
    municipal_status: str = "not_assessed",
    action_status: str = "none_reported",
) -> list[str]:
    return [
        record_id,
        report_type,
        reported_at,
        longitude,
        latitude,
        location_precision,
        review_status,
        municipal_status,
        action_status,
    ]


def _write_csv(
    tmp_path: Path,
    rows: list[list[str]],
    *,
    header: list[str] | None = None,
) -> tuple[Path, str]:
    path = tmp_path / "reports.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header if header is not None else COLUMNS)
        writer.writerows(rows)
    return path, compute_file_sha256(path)


def _load(source: Path, sha256: str):
    return load_and_validate_source(
        source,
        expected_sha256=sha256,
        dataset_id=FIXTURE_DATASET_ID,
        resource_version=FIXTURE_RESOURCE_VERSION,
    )


def test_committed_fixture_hash_and_records_match_manifest() -> None:
    assert compute_file_sha256(FIXTURE_PATH) == FIXTURE_SHA256
    batch = _load(FIXTURE_PATH, FIXTURE_SHA256)
    assert len(batch.records) == 5
    assert batch.records[0].source_record_id == "RR-0001"
    assert {record.location_precision for record in batch.records} == {"synthetic_point"}
    assert {record.review_status for record in batch.records} == {"unreviewed"}
    assert {record.municipal_status for record in batch.records} == {"not_assessed"}
    assert {record.action_status for record in batch.records} == {"none_reported"}


def test_valid_synthetic_csv_parses_records(tmp_path: Path) -> None:
    source, sha256 = _write_csv(tmp_path, [_row("RR-1"), _row("RR-2", report_type="unknown")])
    batch = _load(source, sha256)
    assert [record.source_record_id for record in batch.records] == ["RR-1", "RR-2"]
    assert batch.records[0].longitude == 121.5265
    assert batch.content_sha256 == sha256


def test_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    source, _ = _write_csv(tmp_path, [_row()])
    with pytest.raises(RodentReportImportError, match="SHA-256 mismatch"):
        _load(source, "0" * 64)


def test_unknown_or_forbidden_column_is_rejected(tmp_path: Path) -> None:
    header = [*COLUMNS, "name"]
    source, sha256 = _write_csv(tmp_path, [[*_row(), "Jane"]], header=header)
    with pytest.raises(RodentReportImportError, match="header must be exactly"):
        _load(source, sha256)


def test_missing_column_is_rejected(tmp_path: Path) -> None:
    header = COLUMNS[:-1]
    source, sha256 = _write_csv(tmp_path, [_row()[:-1]], header=header)
    with pytest.raises(RodentReportImportError, match="header must be exactly"):
        _load(source, sha256)


def test_reordered_header_is_rejected(tmp_path: Path) -> None:
    header = list(reversed(COLUMNS))
    source, sha256 = _write_csv(tmp_path, [list(reversed(_row()))], header=header)
    with pytest.raises(RodentReportImportError, match="header must be exactly"):
        _load(source, sha256)


def test_empty_source_record_id_is_rejected(tmp_path: Path) -> None:
    source, sha256 = _write_csv(tmp_path, [_row("")])
    with pytest.raises(RodentReportImportError, match="empty source_record_id"):
        _load(source, sha256)


def test_duplicate_source_record_id_is_rejected(tmp_path: Path) -> None:
    source, sha256 = _write_csv(tmp_path, [_row("RR-1"), _row("RR-1")])
    with pytest.raises(RodentReportImportError, match="duplicate source_record_id"):
        _load(source, sha256)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("report_type", "observation"),
        ("report_type", ""),
        ("location_precision", "exact"),
        ("review_status", "approved"),
        ("municipal_status", "confirmed"),
        ("action_status", "treated"),
    ],
)
def test_invalid_enum_is_rejected(tmp_path: Path, field: str, value: str) -> None:
    row = _row()
    row[COLUMNS.index(field)] = value
    source, sha256 = _write_csv(tmp_path, [row])
    with pytest.raises(RodentReportImportError, match="disallowed or empty"):
        _load(source, sha256)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("longitude", "181.0"),
        ("longitude", "-181.0"),
        ("latitude", "91.0"),
        ("latitude", "-91.0"),
        ("longitude", "not-a-number"),
        ("latitude", "nan"),
    ],
)
def test_invalid_coordinate_is_rejected(tmp_path: Path, field: str, value: str) -> None:
    row = _row()
    row[COLUMNS.index(field)] = value
    source, sha256 = _write_csv(tmp_path, [row])
    with pytest.raises(RodentReportImportError, match="longitude|latitude"):
        _load(source, sha256)


@pytest.mark.parametrize("value", ["2026-10-01", "2026-10-01T08:15:00", "not-a-time", ""])
def test_invalid_timestamp_is_rejected(tmp_path: Path, value: str) -> None:
    row = _row(reported_at=value)
    source, sha256 = _write_csv(tmp_path, [row])
    with pytest.raises(RodentReportImportError, match="reported_at"):
        _load(source, sha256)


def test_provenance_matches_typed_envelope(tmp_path: Path) -> None:
    source, sha256 = _write_csv(tmp_path, [_row()])
    batch = _load(source, sha256)
    provenance = build_provenance(batch)
    assert provenance.source_kind == "synthetic_fixture"
    assert provenance.synthetic is True
    assert provenance.content_sha256 == sha256
    assert provenance.dataset_id == FIXTURE_DATASET_ID
    assert provenance.source_crs == provenance.target_crs == "EPSG:4326"


def test_provenance_model_is_immutable(tmp_path: Path) -> None:
    source, sha256 = _write_csv(tmp_path, [_row()])
    provenance = build_provenance(_load(source, sha256))
    with pytest.raises(ValidationError):
        provenance.content_sha256 = "0" * 64


def test_model_defines_expected_columns_and_constraints() -> None:
    table = cast(Table, RodentReport.__table__)
    assert set(table.columns.keys()) >= {
        "source_record_id",
        "dataset_id",
        "resource_version",
        "content_sha256",
        "data_class",
        "classification",
        "report_type",
        "reported_at",
        "location_precision",
        "review_status",
        "municipal_status",
        "action_status",
        "geometry",
    }
    unique_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
        and {column.name for column in constraint.columns}
        == {"dataset_id", "resource_version", "source_record_id"}
    ]
    assert unique_constraints
    check_sql = " ".join(
        str(constraint.sqltext)
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    )
    assert "RODENT_REPORT" in check_sql
    assert "POINT" in check_sql
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
        return inspect(engine).has_table("rodent_reports")
    except SQLAlchemyError:
        return False


@pytest.mark.skipif(not _postgis_available(), reason="PostGIS unavailable")
@pytest.mark.skipif(not _table_exists(), reason="rodent_reports migration not applied")
def test_persist_import_is_idempotent_and_fail_closed(tmp_path: Path) -> None:
    from ratsight_api.importers.rodent_reports import persist_import

    source, sha256 = _write_csv(tmp_path, [_row("RR-1"), _row("RR-2")])
    batch = _load(source, sha256)
    provenance = build_provenance(batch)
    with SessionLocal() as session:
        try:
            first = persist_import(session, batch, provenance)
            assert first.inserted == 2
            second = persist_import(session, batch, provenance)
            assert second.unchanged == 2

            changed_source, changed_sha = _write_csv(
                tmp_path, [_row("RR-1", report_type="nuisance_report"), _row("RR-2")]
            )
            changed = _load(changed_source, changed_sha)
            with pytest.raises(RodentReportConflictError, match="content changed"):
                persist_import(session, changed, provenance)

            omitted_source, omitted_sha = _write_csv(tmp_path, [_row("RR-1")])
            omitted = _load(omitted_source, omitted_sha)
            with pytest.raises(RodentReportConflictError, match="identity set changed"):
                persist_import(session, omitted, provenance)

            row = session.execute(
                text(
                    "SELECT DISTINCT data_class, classification FROM rodent_reports "
                    "WHERE dataset_id = :d"
                ),
                {"d": FIXTURE_DATASET_ID},
            ).all()
            assert {tuple(item) for item in row} == {
                (RODENT_REPORT_DATA_CLASS, RODENT_REPORT_CLASSIFICATION)
            }
        finally:
            session.rollback()


@pytest.mark.skipif(not _postgis_available(), reason="PostGIS unavailable")
@pytest.mark.skipif(not _table_exists(), reason="rodent_reports migration not applied")
def test_bbox_and_time_filter_select_matching_points(tmp_path: Path) -> None:
    from ratsight_api.application.rodent_reports import list_rodent_reports
    from ratsight_api.importers.rodent_reports import persist_import

    source, sha256 = _write_csv(
        tmp_path,
        [
            _row("RR-1", reported_at="2026-10-01T00:00:00Z", longitude="121.50", latitude="25.00"),
            _row("RR-2", reported_at="2026-10-05T00:00:00Z", longitude="121.60", latitude="25.10"),
        ],
    )
    batch = _load(source, sha256)
    provenance = build_provenance(batch)
    with SessionLocal() as session:
        try:
            persist_import(session, batch, provenance)
            session.flush()
            response = list_rodent_reports(
                session,
                bbox="121.45,24.95,121.55,25.05",
                dataset_id=FIXTURE_DATASET_ID,
            )
            assert response.data_state == "available"
            assert [feature.id for feature in response.features] == ["RR-1"]
            assert response.bbox == (121.45, 24.95, 121.55, 25.05)

            time_filtered = list_rodent_reports(
                session,
                reported_from="2026-10-04T00:00:00Z",
                reported_to="2026-10-06T00:00:00Z",
                dataset_id=FIXTURE_DATASET_ID,
            )
            assert [feature.id for feature in time_filtered.features] == ["RR-2"]
            assert time_filtered.reported_from == "2026-10-04T00:00:00Z"

            miss = list_rodent_reports(
                session,
                bbox="121.0,24.0,121.05,24.05",
                dataset_id=FIXTURE_DATASET_ID,
            )
            assert miss.data_state == "available"
            assert miss.feature_count == 0
            assert miss.provenance is not None
        finally:
            session.rollback()


def _unused(value: Any) -> None:  # pragma: no cover
    del value
