"""Database-free tests for the suppressed citizen-report aggregate importer."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

import pytest
from ratsight_api.domain.citizen_report_aggregates import (
    ATTRIBUTION,
    CELL_SIZE_METERS,
    CITIZEN_REPORT_CLASSIFICATION,
    CITIZEN_REPORT_DATA_CLASS,
    DROPPED_COLUMNS,
    RAW_COLUMNS,
    SUPPRESSION_MINIMUM,
)
from ratsight_api.importers.citizen_report_aggregates import (
    CitizenReportImportError,
    _with_reused_version,
    aggregate_export,
    build_provenance,
    compute_file_sha256,
)

COLUMNS = list(RAW_COLUMNS)
PRIVATE_PLACE = "某大樓三樓住戶前陽台"
PRIVATE_NOTE = "我家廚房後面看到老鼠"
PRIVATE_PHOTO = "https://example.invalid/private-photo.jpg"


def _row(
    *,
    reported_at: str = "2026-05-04 09:30:00",
    report_type: str = "鼠蹤",
    latitude: str = "25.0330",
    longitude: str = "121.5265",
) -> list[str]:
    return [
        reported_at,
        report_type,
        PRIVATE_PLACE,
        "已審核",
        PRIVATE_NOTE,
        PRIVATE_PHOTO,
        latitude,
        longitude,
    ]


def _write_csv(tmp_path: Path, rows: list[list[str]]) -> Path:
    path = tmp_path / "citizen-reports.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    return path


def test_cell_month_counts_are_suppressed_below_the_minimum(tmp_path: Path) -> None:
    source = _write_csv(
        tmp_path,
        [
            _row(),
            _row(),
            _row(),
            _row(latitude="25.0700", longitude="121.5600"),
            _row(latitude="25.0701", longitude="121.5601"),
        ],
    )
    batch = aggregate_export(source)

    assert len(batch.rows) == 1
    row = batch.rows[0]
    assert row.count == 3
    assert row.month == "2026-05"
    assert row.report_type == "sighting"
    assert batch.parsed == 5
    assert batch.used == 3
    assert batch.suppressed_records == 2
    assert batch.suppressed_cells == 1


def test_private_text_and_photo_urls_never_reach_the_batch(tmp_path: Path) -> None:
    source = _write_csv(tmp_path, [_row(), _row(), _row()])
    batch = aggregate_export(source)
    rendered = json.dumps([asdict(row) for row in batch.rows], ensure_ascii=False)

    assert PRIVATE_PLACE not in rendered
    assert PRIVATE_NOTE not in rendered
    assert PRIVATE_PHOTO not in rendered
    assert PRIVATE_PLACE not in str(build_provenance(batch).model_dump(mode="json"))


def test_low_count_report_type_rows_are_dropped(tmp_path: Path) -> None:
    source = _write_csv(
        tmp_path,
        [_row(), _row(), _row(), _row(report_type="毒餌")],
    )
    batch = aggregate_export(source)

    assert [row.report_type for row in batch.rows] == ["sighting"]
    assert batch.rows[0].count == 3
    assert batch.suppressed_records == 1


def test_invalid_coordinates_are_counted_not_aggregated(tmp_path: Path) -> None:
    source = _write_csv(
        tmp_path,
        [_row(), _row(), _row(), _row(latitude="not-a-number")],
    )
    batch = aggregate_export(source)

    assert batch.parsed == 4
    assert batch.invalid_coordinates == 1
    assert batch.used == 3


def test_wall_clock_month_bucket_is_used(tmp_path: Path) -> None:
    source = _write_csv(
        tmp_path,
        [
            _row(reported_at="2026-05-31 23:59:00"),
            _row(reported_at="2026-05-31 22:00:00"),
            _row(reported_at="2026-05-30 08:00:00"),
            _row(reported_at="2026-06-01 00:01:00"),
            _row(reported_at="2026-06-02 08:00:00"),
            _row(reported_at="2026-06-03 09:00:00"),
        ],
    )
    batch = aggregate_export(source)

    months = sorted({(row.month, row.count) for row in batch.rows})
    assert months == [("2026-05", 3), ("2026-06", 3)]


def test_cell_geometry_is_a_suppression_sized_grid_cell(tmp_path: Path) -> None:
    source = _write_csv(tmp_path, [_row(), _row(), _row()])
    row = aggregate_export(source).rows[0]

    assert row.cell_id.startswith(f"g{CELL_SIZE_METERS}m:")
    assert row.west < row.east and row.south < row.north
    assert 0.002 < (row.north - row.south) < 0.003


def test_provenance_marks_unverified_aggregate_and_dropped_fields(tmp_path: Path) -> None:
    source = _write_csv(tmp_path, [_row(), _row(), _row()])
    batch = aggregate_export(source)
    provenance = build_provenance(batch)

    assert provenance.source_kind == "public_citizen_report_export"
    assert provenance.aggregation.suppression_minimum == SUPPRESSION_MINIMUM
    assert provenance.aggregation.cell_size_meters == CELL_SIZE_METERS
    assert list(provenance.aggregation.dropped_fields) == list(DROPPED_COLUMNS)
    assert provenance.counts.parsed == 3
    assert provenance.counts.used == 3
    assert provenance.synthetic is False
    assert provenance.attribution == ATTRIBUTION
    assert CITIZEN_REPORT_DATA_CLASS == "CITIZEN_REPORT_AGGREGATE"
    assert CITIZEN_REPORT_CLASSIFICATION == "UNVERIFIED"


def test_repeated_import_reuses_the_stored_version(tmp_path: Path) -> None:
    source = _write_csv(tmp_path, [_row(), _row(), _row()])
    batch = aggregate_export(source)

    assert _with_reused_version(batch, None) is batch
    assert _with_reused_version(batch, batch.resource_version) is batch

    reused = _with_reused_version(batch, "2026-10-26T17:22:26Z")
    assert reused.resource_version == "2026-10-26T17:22:26Z"
    assert reused.retrieved_at == batch.retrieved_at
    assert reused.content_sha256 == batch.content_sha256
    assert reused.rows == batch.rows


def test_content_hash_is_recorded(tmp_path: Path) -> None:
    source = _write_csv(tmp_path, [_row(), _row(), _row()])
    batch = aggregate_export(source)
    assert batch.content_sha256 == compute_file_sha256(source)


def test_missing_column_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS[:-1])
        writer.writerow(_row()[:-1])
    with pytest.raises(CitizenReportImportError, match="missing required columns"):
        aggregate_export(path)


def test_nothing_surviving_suppression_is_rejected(tmp_path: Path) -> None:
    source = _write_csv(tmp_path, [_row(), _row()])
    with pytest.raises(CitizenReportImportError, match="suppression minimum"):
        aggregate_export(source)
