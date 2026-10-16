"""API contract tests for the stormwater infrastructure reference endpoint."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from ratsight_api.api.routes import stormwater_pipelines as route_module
from ratsight_api.api.schemas import (
    StormwaterProcessing,
    StormwaterProvenanceV1,
    StormwaterSourceQuality,
    StormwaterUncertainty,
)
from ratsight_api.application.stormwater_pipelines import (
    list_stormwater_pipelines,
    parse_bbox,
)
from ratsight_api.domain.stormwater import (
    OFFICIAL_DATASET_ID,
    OFFICIAL_RESOURCE_ID,
    OFFICIAL_RESOURCE_VERSION,
    STORMWATER_CLASSIFICATION,
    STORMWATER_DATA_CLASS,
)
from ratsight_api.infrastructure.database.connection import get_session
from ratsight_api.main import app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

ENDPOINT = "/api/v1/stormwater-pipelines"
ARCHIVE_SHA = "a" * 64
VALID_LINESTRING: dict[str, Any] = {
    "type": "LineString",
    "coordinates": [[121.50, 25.00], [121.51, 25.01]],
}

REQUIRED_PROPERTY_KEYS = {
    "segment_id",
    "data_class",
    "classification",
    "provenance_schema_version",
    "dataset_id",
    "resource_version",
    "archive_sha256",
}
OPTIONAL_ATTRIBUTE_KEYS = {
    "category_code",
    "pipe_number",
    "start_node_id",
    "end_node_id",
    "managing_unit",
    "work_category",
    "installation_date",
    "dimension_unit",
    "diameter_width",
    "diameter_height",
    "conduit_count",
    "material",
    "start_burial_depth",
    "end_burial_depth",
    "length",
    "pipe_type",
    "use_status",
    "data_status",
    "notes",
}


def _provenance() -> StormwaterProvenanceV1:
    return StormwaterProvenanceV1(
        schema_version="1",
        source_url="https://example.test/source",
        download_url="https://example.test/download",
        dataset_id=OFFICIAL_DATASET_ID,
        resource_id=OFFICIAL_RESOURCE_ID,
        resource_version=OFFICIAL_RESOURCE_VERSION,
        retrieved_at="2026-10-16T00:00:00Z",
        archive_sha256=ARCHIVE_SHA,
        license="Open Government Data License v1",
        attribution="Taipei City Government Public Works Department",
        source_crs="EPSG:3826",
        target_crs="EPSG:4326",
        z_handling="dropped",
        processing=StormwaterProcessing(tool="test", tool_version="1", steps=["validated fixture"]),
        source_quality=StormwaterSourceQuality(
            reference_only=True,
            missing_pipe_number_count=0,
            duplicate_pipe_number_value_count=0,
            missing_start_endpoint_count=0,
            missing_end_endpoint_count=0,
            missing_notes_count=0,
        ),
        uncertainty=StormwaterUncertainty(currentness="unverified", note="reference only"),
    )


def _meta_row() -> dict[str, Any]:
    return {
        "resource_version": OFFICIAL_RESOURCE_VERSION,
        "archive_sha256": ARCHIVE_SHA,
        "provenance": _provenance().model_dump(mode="json"),
    }


def _feature_row(geometry: Any = None, **overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "source_record_id": "P001",
        "dataset_id": OFFICIAL_DATASET_ID,
        "resource_version": OFFICIAL_RESOURCE_VERSION,
        "archive_sha256": ARCHIVE_SHA,
        "geometry": json.dumps(VALID_LINESTRING if geometry is None else geometry),
        "pipe_number": "PN1",
        "material": "RCP",
    }
    for name in OPTIONAL_ATTRIBUTE_KEYS:
        row.setdefault(name, None)
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
    session = cast(Session, _FakeSession(results))
    return list_stormwater_pipelines(session, **kwargs)


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _no_leaked_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def test_empty_storage_is_honest_empty_state() -> None:
    response = _list([[]])
    assert response.data_state == "empty"
    assert response.provenance is None
    assert response.feature_count == 0
    assert response.features == []
    assert response.truncated is False


def test_available_returns_allowlist_properties() -> None:
    response = _list([[_meta_row()], [_feature_row()]])
    assert response.data_state == "available"
    assert response.provenance is not None
    assert response.feature_count == 1
    feature = response.features[0]
    properties = feature.properties.model_dump(exclude_none=True)
    assert set(properties) <= REQUIRED_PROPERTY_KEYS | OPTIONAL_ATTRIBUTE_KEYS
    assert REQUIRED_PROPERTY_KEYS <= set(properties)
    assert properties["classification"] == STORMWATER_CLASSIFICATION
    assert properties["data_class"] == STORMWATER_DATA_CLASS
    assert properties["pipe_number"] == "PN1"
    assert "start_node_id" not in properties
    assert feature.geometry.type == "LineString"


def test_bbox_miss_is_available_with_zero_features() -> None:
    response = _list([[_meta_row()], []], bbox=(121.5, 25.0, 121.6, 25.1))
    assert response.data_state == "available"
    assert response.provenance is not None
    assert response.feature_count == 0
    assert response.features == []
    assert response.bbox == (121.5, 25.0, 121.6, 25.1)


def test_result_cap_sets_truncated(monkeypatch: pytest.MonkeyPatch) -> None:
    import ratsight_api.application.stormwater_pipelines as application

    monkeypatch.setattr(application, "FEATURE_CAP", 2)
    response = _list([[_meta_row()], [_feature_row(), _feature_row(), _feature_row()]])
    assert response.feature_count == 2
    assert len(response.features) == 2
    assert response.truncated is True


def test_storage_failure_raises_storage_error() -> None:
    from ratsight_api.application.stormwater_pipelines import StormwaterStorageError

    with pytest.raises(StormwaterStorageError):
        _list([SQLAlchemyError("down")])


def test_malformed_persisted_geometry_raises_data_error() -> None:
    from ratsight_api.application.stormwater_pipelines import StormwaterDataError

    bad = {"type": "LineString", "coordinates": [[121.5, 25.0]]}
    with pytest.raises(StormwaterDataError, match="geometry is invalid"):
        _list([[_meta_row()], [_feature_row(bad)]])


def test_mixed_source_group_raises_data_error() -> None:
    from ratsight_api.application.stormwater_pipelines import StormwaterDataError

    with pytest.raises(StormwaterDataError, match="multiple source groups"):
        _list([[_meta_row()], [_feature_row(resource_version="2026-01-01T00:00:00Z")]])


@pytest.mark.parametrize(
    "value",
    [
        "121.5,25.0,121.6",
        "a,b,c,d",
        "nan,25.0,121.6,25.1",
        "-181,25.0,121.6,25.1",
        "121.6,25.0,121.5,25.1",
        "121.0,25.0,121.5,25.1",
        "121.5,25.0,121.6,25.5",
    ],
)
def test_parse_bbox_rejects_invalid(value: str) -> None:
    from ratsight_api.application.stormwater_pipelines import StormwaterQueryError

    with pytest.raises(StormwaterQueryError):
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
    assert response.headers["content-type"].startswith("application/geo+json")


@pytest.mark.asyncio
async def test_route_invalid_bbox_is_422(client: AsyncClient) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession([[]])
    response = await client.get(ENDPOINT, params={"bbox": "121.5,25.0,121.6"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_route_storage_failure_is_503(client: AsyncClient) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession([SQLAlchemyError("down")])
    response = await client.get(ENDPOINT)
    assert response.status_code == 503
    assert response.json() == {"detail": route_module.STORAGE_UNAVAILABLE_DETAIL}


@pytest.mark.asyncio
async def test_route_malformed_geometry_is_500(client: AsyncClient) -> None:
    bad = {"type": "LineString", "coordinates": [[121.5, 25.0]]}
    app.dependency_overrides[get_session] = lambda: _FakeSession(
        [[_meta_row()], [_feature_row(bad)]]
    )
    response = await client.get(ENDPOINT)
    assert response.status_code == 500
    assert response.json() == {"detail": route_module.INVALID_DATA_DETAIL}


@pytest.mark.asyncio
async def test_route_available_serializes_null_attributes_as_omitted(client: AsyncClient) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession([[_meta_row()], [_feature_row()]])
    response = await client.get(ENDPOINT, params={"bbox": "121.5,25.0,121.6,25.1"})
    assert response.status_code == 200
    payload = response.json()
    properties = payload["features"][0]["properties"]
    assert REQUIRED_PROPERTY_KEYS <= set(properties)
    assert "start_node_id" not in properties
    assert payload["bbox"] == [121.5, 25.0, 121.6, 25.1]
    assert payload["truncated"] is False


@pytest.mark.asyncio
async def test_openapi_contains_stormwater_route(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    assert ENDPOINT in schema["paths"]
