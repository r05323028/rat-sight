"""API contract tests for the fixture-only rodent report endpoint."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any, cast

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from ratsight_api.api.routes import rodent_reports as route_module
from ratsight_api.api.schemas import (
    RodentReportProcessing,
    RodentReportProvenanceV1,
    RodentReportUncertainty,
)
from ratsight_api.application.rodent_reports import (
    list_rodent_reports,
    parse_bbox,
)
from ratsight_api.domain.rodent_reports import (
    FIXTURE_DATASET_ID,
    FIXTURE_RESOURCE_VERSION,
    RODENT_REPORT_CLASSIFICATION,
    RODENT_REPORT_DATA_CLASS,
)
from ratsight_api.infrastructure.database.connection import get_session
from ratsight_api.main import app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

ENDPOINT = "/api/v1/rodent-reports"
CONTENT_SHA = "b" * 64
VALID_POINT: dict[str, Any] = {"type": "Point", "coordinates": [121.5265, 25.0330]}

PROPERTY_KEYS = {
    "report_id",
    "source",
    "report_type",
    "reported_at",
    "location_precision",
    "review_status",
    "municipal_status",
    "action_status",
    "data_class",
    "classification",
    "provenance_schema_version",
    "dataset_id",
    "resource_version",
    "content_sha256",
}


def _provenance() -> RodentReportProvenanceV1:
    return RodentReportProvenanceV1(
        schema_version="1",
        source_kind="synthetic_fixture",
        dataset_id=FIXTURE_DATASET_ID,
        resource_version=FIXTURE_RESOURCE_VERSION,
        retrieved_at="2026-10-17T00:00:00Z",
        content_sha256=CONTENT_SHA,
        license="Synthetic fixture only.",
        attribution="RatSight synthetic rodent-report fixture",
        source_crs="EPSG:4326",
        target_crs="EPSG:4326",
        processing=RodentReportProcessing(tool="test", tool_version="1", steps=["fixture"]),
        synthetic=True,
        uncertainty=RodentReportUncertainty(currentness="synthetic", note="not an observation"),
    )


def _meta_row() -> dict[str, Any]:
    return {
        "resource_version": FIXTURE_RESOURCE_VERSION,
        "content_sha256": CONTENT_SHA,
        "provenance": _provenance().model_dump(mode="json"),
    }


def _feature_row(geometry: Any = None, **overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "source_record_id": "RR-0001",
        "dataset_id": FIXTURE_DATASET_ID,
        "resource_version": FIXTURE_RESOURCE_VERSION,
        "content_sha256": CONTENT_SHA,
        "report_type": "sighting_report",
        "reported_at": datetime(2026, 10, 1, 8, 15, tzinfo=UTC),
        "location_precision": "synthetic_point",
        "review_status": "unreviewed",
        "municipal_status": "not_assessed",
        "action_status": "none_reported",
        "provenance": _provenance().model_dump(mode="json"),
        "geometry": json.dumps(VALID_POINT if geometry is None else geometry),
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
    return list_rodent_reports(cast(Session, _FakeSession(results)), **kwargs)


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _no_leaked_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def test_empty_storage_distinguishes_from_filter_empty() -> None:
    response = _list([[]], bbox="121.5,25.0,121.6,25.1")
    assert response.data_state == "empty"
    assert response.provenance is None
    assert response.features == []
    assert response.feature_count == 0
    assert response.bbox == (121.5, 25.0, 121.6, 25.1)


def test_available_returns_exact_property_keys() -> None:
    response = _list([[_meta_row()], [_feature_row()]])
    assert response.data_state == "available"
    assert response.provenance is not None
    assert response.feature_count == 1
    feature = response.features[0]
    properties = feature.properties.model_dump()
    assert set(properties) == PROPERTY_KEYS
    assert "source_record_id" not in properties
    assert "longitude" not in properties
    assert "latitude" not in properties
    assert properties["report_id"] == "RR-0001"
    assert properties["source"] == "synthetic_fixture"
    assert properties["classification"] == RODENT_REPORT_CLASSIFICATION
    assert properties["data_class"] == RODENT_REPORT_DATA_CLASS
    assert feature.geometry.type == "Point"
    assert feature.geometry.coordinates == [121.5265, 25.033]


def test_filter_miss_is_available_with_zero_features() -> None:
    response = _list(
        [[_meta_row()], []],
        bbox="121.5,25.0,121.6,25.1",
        reported_from="2026-10-01T00:00:00Z",
        reported_to="2026-10-02T00:00:00Z",
    )
    assert response.data_state == "available"
    assert response.provenance is not None
    assert response.feature_count == 0
    assert response.features == []
    assert response.reported_from == "2026-10-01T00:00:00Z"
    assert response.reported_to == "2026-10-02T00:00:00Z"


def test_time_offsets_are_normalized_to_z() -> None:
    response = _list(
        [[_meta_row()], []],
        reported_from="2026-10-01T08:00:00+08:00",
        reported_to="2026-10-02T00:00:00Z",
    )
    assert response.reported_from == "2026-10-01T00:00:00Z"
    assert response.reported_to == "2026-10-02T00:00:00Z"


def test_result_cap_sets_truncated(monkeypatch: pytest.MonkeyPatch) -> None:
    import ratsight_api.application.rodent_reports as application

    monkeypatch.setattr(application, "FEATURE_CAP", 2)
    response = _list([[_meta_row()], [_feature_row(), _feature_row(), _feature_row()]])
    assert response.feature_count == 2
    assert response.truncated is True


def test_storage_failure_raises_storage_error() -> None:
    from ratsight_api.application.rodent_reports import RodentReportStorageError

    with pytest.raises(RodentReportStorageError):
        _list([SQLAlchemyError("down")])


def test_malformed_persisted_geometry_raises_data_error() -> None:
    from ratsight_api.application.rodent_reports import RodentReportDataError

    with pytest.raises(RodentReportDataError, match="geometry is invalid"):
        _list([[_meta_row()], [_feature_row({"type": "Point", "coordinates": [999, 25]})]])


def test_mixed_source_group_raises_data_error() -> None:
    from ratsight_api.application.rodent_reports import RodentReportDataError

    other_provenance = _provenance().model_dump(mode="json")
    other_provenance["attribution"] = "Other fixture attribution"
    with pytest.raises(RodentReportDataError, match="multiple source groups"):
        _list([[_meta_row()], [_feature_row(provenance=other_provenance)]])


def test_from_after_to_is_rejected() -> None:
    from ratsight_api.application.rodent_reports import RodentReportQueryError

    with pytest.raises(RodentReportQueryError, match="reported_from"):
        _list(
            [[_meta_row()], []],
            reported_from="2026-10-05T00:00:00Z",
            reported_to="2026-10-01T00:00:00Z",
        )


@pytest.mark.parametrize(
    "value",
    [
        "121.5,25.0,121.6",
        "a,b,c,d",
        "121.6,25.0,121.5,25.1",
        "121.0,25.0,121.5,25.1",
        "nan,25.0,121.6,25.1",
    ],
)
def test_parse_bbox_rejects_invalid(value: str) -> None:
    from ratsight_api.application.rodent_reports import RodentReportQueryError

    with pytest.raises(RodentReportQueryError):
        parse_bbox(value)


def test_parse_bbox_accepts_valid() -> None:
    assert parse_bbox("121.5,25.0,121.6,25.1") == (121.5, 25.0, 121.6, 25.1)
    assert parse_bbox(None) is None


@pytest.mark.asyncio
async def test_route_empty_storage(client: AsyncClient) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession([[]])
    response = await client.get(ENDPOINT)
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_state"] == "empty"
    assert payload["provenance"] is None
    assert payload["feature_count"] == 0
    assert payload["reported_from"] is None
    assert response.headers["content-type"].startswith("application/geo+json")


@pytest.mark.asyncio
async def test_route_invalid_bbox_is_422(client: AsyncClient) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession([[]])
    response = await client.get(ENDPOINT, params={"bbox": "121.5,25.0,121.6"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_route_invalid_time_is_422(client: AsyncClient) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession([[]])
    response = await client.get(ENDPOINT, params={"reported_from": "yesterday"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_route_storage_failure_is_503(client: AsyncClient) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession([SQLAlchemyError("down")])
    response = await client.get(ENDPOINT)
    assert response.status_code == 503
    assert response.json() == {"detail": route_module.STORAGE_UNAVAILABLE_DETAIL}


@pytest.mark.asyncio
async def test_route_available_serialization(client: AsyncClient) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession([[_meta_row()], [_feature_row()]])
    response = await client.get(
        ENDPOINT,
        params={"bbox": "121.5,25.0,121.6,25.1", "reported_from": "2026-10-01T00:00:00Z"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_class"] == RODENT_REPORT_DATA_CLASS
    assert payload["classification"] == RODENT_REPORT_CLASSIFICATION
    assert payload["features"][0]["geometry"]["type"] == "Point"
    assert set(payload["features"][0]["properties"]) == PROPERTY_KEYS
    assert payload["bbox"] == [121.5, 25.0, 121.6, 25.1]
    assert payload["reported_from"] == "2026-10-01T00:00:00Z"


@pytest.mark.asyncio
async def test_openapi_contains_rodent_reports_route(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    assert ENDPOINT in schema["paths"]
