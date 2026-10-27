"""API contract tests for the suppressed citizen-report aggregate endpoint."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from ratsight_api.api.routes import citizen_report_aggregates as route_module
from ratsight_api.api.schemas import (
    CitizenReportAggregation,
    CitizenReportCounts,
    CitizenReportProcessing,
    CitizenReportProvenanceV1,
    CitizenReportUncertainty,
)
from ratsight_api.application.citizen_report_aggregates import (
    CitizenReportCellNotFound,
    CitizenReportDataError,
    CitizenReportQueryError,
    CitizenReportStorageError,
    get_citizen_report_cell_polygon,
    list_citizen_report_aggregates,
    parse_bbox,
    parse_months,
)
from ratsight_api.domain.citizen_report_aggregates import (
    ATTRIBUTION,
    DATASET_ID,
    SUPPRESSION_MINIMUM,
)
from ratsight_api.infrastructure.database.connection import get_session
from ratsight_api.main import app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

ENDPOINT = "/api/v1/citizen-report-aggregates"
CONTENT_SHA = "c" * 64
VERSION = "2026-10-26T20:00:00Z"
POLYGON: dict[str, Any] = {
    "type": "Polygon",
    "coordinates": [
        [
            [121.5100, 25.0112],
            [121.5100, 25.0135],
            [121.5080, 25.0135],
            [121.5080, 25.0112],
            [121.5100, 25.0112],
        ]
    ],
}
PROPERTY_KEYS = {
    "cell_id",
    "month",
    "report_type",
    "count",
    "data_class",
    "classification",
    "attribution",
}


def _provenance() -> CitizenReportProvenanceV1:
    return CitizenReportProvenanceV1(
        schema_version="1",
        source_kind="public_citizen_report_export",
        dataset_id=DATASET_ID,
        resource_version=VERSION,
        retrieved_at=VERSION,
        content_sha256=CONTENT_SHA,
        source_url="https://ratdar.taipei/",
        license="public export without reuse terms; aggregates only",
        attribution=ATTRIBUTION,
        source_crs="EPSG:4326",
        target_crs="EPSG:4326",
        processing=CitizenReportProcessing(tool="test", tool_version="1", steps=["aggregate"]),
        aggregation=CitizenReportAggregation(
            cell_size_meters=250,
            month_timezone_assumption="Asia/Taipei wall clock",
            suppression_minimum=SUPPRESSION_MINIMUM,
            dropped_fields=["地點", "說明", "照片網址"],
        ),
        counts=CitizenReportCounts(
            parsed=10,
            used=3,
            invalid_coordinates=0,
            suppressed_records=7,
            suppressed_cells=2,
        ),
        synthetic=False,
        uncertainty=CitizenReportUncertainty(currentness=VERSION, note="not observation"),
    )


def _meta_row() -> dict[str, Any]:
    return {"resource_version": VERSION, "provenance": _provenance().model_dump(mode="json")}


def _feature_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "cell_id": "g250m:1:2",
        "month": "2026-05",
        "report_type": "sighting",
        "report_count": 3,
        "data_class": "CITIZEN_REPORT_AGGREGATE",
        "classification": "UNVERIFIED",
        "geometry": json.dumps(POLYGON),
    }
    row.update(overrides)
    return row


class _FakeMappings:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def first(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def all(self) -> list[dict[str, Any]]:
        return list(self._rows)


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> _FakeMappings:
        return _FakeMappings(self._rows)


class _FakeSession:
    def __init__(self, results: list[Any]) -> None:
        self._results = list(results)

    def execute(self, statement: object) -> _FakeResult:
        if not self._results:
            raise AssertionError("unexpected extra execute")
        nxt = self._results.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return _FakeResult(cast(list[dict[str, Any]], nxt))


def _list(results: list[Any], **kwargs: Any):
    return list_citizen_report_aggregates(cast(Session, _FakeSession(results)), **kwargs)


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _no_leaked_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def test_empty_storage_is_distinct_from_a_filter_miss() -> None:
    response = _list([[]], bbox="121.5,25.0,121.6,25.1")
    assert response.data_state == "empty"
    assert response.provenance is None
    assert response.feature_count == 0
    assert response.bbox == (121.5, 25.0, 121.6, 25.1)


def test_available_response_exposes_counts_not_reports() -> None:
    response = _list([[_meta_row()], [_feature_row()]])
    assert response.data_state == "available"
    assert response.feature_count == 1
    properties = response.features[0].properties.model_dump()
    assert set(properties) == PROPERTY_KEYS
    assert properties["count"] == 3
    assert properties["classification"] == "UNVERIFIED"
    assert properties["attribution"] == ATTRIBUTION
    assert response.features[0].geometry.type == "Polygon"
    assert len(response.features[0].geometry.coordinates[0]) == 5


def test_filter_miss_keeps_available_provenance() -> None:
    response = _list([[_meta_row()], []], months="2026-09")
    assert response.data_state == "empty"
    assert response.provenance is not None
    assert response.provenance.source_kind == "public_citizen_report_export"
    assert response.feature_count == 0


@pytest.mark.parametrize(
    "bbox",
    ["121.5,25.0,121.6", "a,b,c,d", "121.6,25.0,121.5,25.1", "118.0,25.0,121.6,25.1"],
)
def test_malformed_bbox_is_rejected(bbox: str) -> None:
    with pytest.raises(CitizenReportQueryError):
        parse_bbox(bbox)


def test_month_buckets_are_validated_and_sorted() -> None:
    assert parse_months("2026-05,2026-04,2026-05") == ("2026-04", "2026-05")
    with pytest.raises(CitizenReportQueryError):
        parse_months("2026-13")
    with pytest.raises(CitizenReportQueryError):
        parse_months("")


def test_invalid_data_class_fails_closed() -> None:
    with pytest.raises(CitizenReportDataError):
        _list([[_meta_row()], [_feature_row(data_class="ADMINISTRATIVE_REFERENCE")]])


def test_origin_cell_resolver_returns_the_exact_stored_polygon() -> None:
    polygon = get_citizen_report_cell_polygon(
        cast(Session, _FakeSession([[_meta_row()], [{"geometry": json.dumps(POLYGON)}]])),
        "g250m:1:2:2026-05:sighting",
    )
    assert polygon.coordinates == POLYGON["coordinates"]


def test_origin_cell_resolver_fails_closed_when_no_version_or_cell_exists() -> None:
    with pytest.raises(CitizenReportCellNotFound, match="no citizen report aggregate version"):
        get_citizen_report_cell_polygon(
            cast(Session, _FakeSession([[]])), "g250m:1:2:2026-05:sighting"
        )
    with pytest.raises(CitizenReportCellNotFound, match="not present in the latest"):
        get_citizen_report_cell_polygon(
            cast(Session, _FakeSession([[_meta_row()], []])), "g250m:1:2:2026-05:sighting"
        )


def test_invalid_classification_fails_closed() -> None:
    with pytest.raises(CitizenReportDataError):
        _list([[_meta_row()], [_feature_row(classification="OBSERVED")]])


def test_storage_failure_is_reported() -> None:
    with pytest.raises(CitizenReportStorageError):
        _list([SQLAlchemyError("boom")])


def test_route_maps_query_errors_to_422(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*args: Any, **kwargs: Any) -> None:
        raise CitizenReportQueryError("bad bbox")

    monkeypatch.setattr(route_module, "list_citizen_report_aggregates", _raise)
    app.dependency_overrides[get_session] = lambda: None
    import asyncio

    async def _call() -> Any:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as test_client:
            return await test_client.get(ENDPOINT, params={"bbox": "bad"})

    response = asyncio.run(_call())
    assert response.status_code == 422
