"""API contract tests for the administrative district boundary endpoint."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any, cast, get_args

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from ratsight_api.api.routes import administrative_districts as route_module
from ratsight_api.api.schemas import (
    AdministrativeDistrictFeature,
    AdministrativeDistrictProperties,
    AdministrativeDistrictResponse,
    Classification,
    GeoJsonGeometry,
    ProvenanceProcessing,
    ProvenanceUncertainty,
    ProvenanceV1,
)
from ratsight_api.application.administrative_districts import (
    AdministrativeDistrictDataError,
    AdministrativeDistrictStorageError,
    list_administrative_districts,
)
from ratsight_api.domain.administrative_districts import (
    ADMINISTRATIVE_DATA_CLASS,
    DISTRICT_CLASSIFICATION,
)
from ratsight_api.infrastructure.database.connection import get_session
from ratsight_api.main import app
from sqlalchemy.orm import Session

ENDPOINT = "/api/v1/administrative-districts"


def _provenance() -> ProvenanceV1:
    return ProvenanceV1(
        schema_version="1",
        source_url="https://example.test/resource",
        dataset_id="121199",
        resource_version="20220915",
        retrieved_at="2026-10-15T00:00:00Z",
        archive_sha256="a" * 64,
        license="Open Government Data License v1",
        attribution="Taipei City Government Department of Civil Affairs",
        processing=ProvenanceProcessing(
            tool="test",
            tool_version="1",
            steps=["validated fixture"],
        ),
        uncertainty=ProvenanceUncertainty(
            currentness="resource version 20220915; legal currency unresolved",
            note="administrative reference geometry only",
        ),
    )


def _available_response() -> AdministrativeDistrictResponse:
    return AdministrativeDistrictResponse(
        features=[
            AdministrativeDistrictFeature(
                id="A",
                properties=AdministrativeDistrictProperties(
                    district_id="A",
                    district_name="中正區",
                    data_class=ADMINISTRATIVE_DATA_CLASS,
                    classification=DISTRICT_CLASSIFICATION,
                    provenance_schema_version="1",
                    dataset_id="121199",
                    resource_version="20220915",
                    archive_sha256="a" * 64,
                ),
                geometry=GeoJsonGeometry(
                    type="Polygon",
                    coordinates=[
                        [[121.50, 25.00], [121.52, 25.00], [121.52, 25.02], [121.50, 25.02]]
                    ],
                ),
            )
        ],
        data_state="available",
        provenance=_provenance(),
    )


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _no_leaked_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_empty_storage_is_honest_200(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        route_module,
        "list_administrative_districts",
        lambda session: AdministrativeDistrictResponse(
            features=[], data_state="empty", provenance=None
        ),
    )
    response = await client.get(ENDPOINT)
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["data_state"] == "empty"
    assert payload["features"] == []
    assert payload["provenance"] is None
    assert response.headers["content-type"].startswith("application/geo+json")


@pytest.mark.asyncio
async def test_available_storage_returns_envelope_with_top_level_provenance(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        route_module,
        "list_administrative_districts",
        lambda session: _available_response(),
    )
    response = await client.get(ENDPOINT)
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_state"] == "available"
    assert payload["data_class"] == ADMINISTRATIVE_DATA_CLASS
    assert payload["provenance"]["schema_version"] == "1"
    feature = payload["features"][0]
    assert feature["id"] == "A"
    assert feature["properties"]["district_name"] == "中正區"
    assert feature["properties"]["classification"] == "UNVERIFIED"
    assert feature["properties"]["provenance_schema_version"] == "1"
    assert "provenance" not in feature["properties"]
    assert feature["geometry"]["type"] == "Polygon"


@pytest.mark.asyncio
async def test_storage_failure_is_503_not_empty(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(session: object) -> AdministrativeDistrictResponse:
        raise AdministrativeDistrictStorageError("unavailable")

    monkeypatch.setattr(route_module, "list_administrative_districts", _raise)
    response = await client.get(ENDPOINT)
    assert response.status_code == 503
    assert response.json() == {"detail": route_module.STORAGE_UNAVAILABLE_DETAIL}


@pytest.mark.asyncio
async def test_malformed_persisted_data_is_explicit_error(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _raise(session: object) -> AdministrativeDistrictResponse:
        raise AdministrativeDistrictDataError("invalid")

    monkeypatch.setattr(route_module, "list_administrative_districts", _raise)
    response = await client.get(ENDPOINT)
    assert response.status_code == 500
    assert response.json() == {"detail": route_module.INVALID_DATA_DETAIL}


@pytest.mark.asyncio
async def test_openapi_contains_administrative_districts_route(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    assert ENDPOINT in schema["paths"]


def test_administrative_reference_is_not_an_epistemic_observation_class() -> None:
    assert ADMINISTRATIVE_DATA_CLASS not in get_args(Classification)
    assert DISTRICT_CLASSIFICATION in get_args(Classification)
    assert DISTRICT_CLASSIFICATION == "UNVERIFIED"


# --- CR-001 / CR-002 regression coverage -------------------------------------
# These tests drive the real application function (not a monkeypatched return)
# with a fake session, so they exercise dataset/version grouping and persisted
# geometry validation.

VALID_GEOMETRY: dict[str, Any] = {
    "type": "Polygon",
    "coordinates": [
        [[121.50, 25.00], [121.52, 25.00], [121.52, 25.02], [121.50, 25.02], [121.50, 25.00]]
    ],
}
VALID_MULTIPOLYGON: dict[str, Any] = {
    "type": "MultiPolygon",
    "coordinates": [
        [[[121.50, 25.00], [121.52, 25.00], [121.52, 25.02], [121.50, 25.02], [121.50, 25.00]]]
    ],
}


class _FakeMappings:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> _FakeMappings:
        return _FakeMappings(self._rows)


class _FakeSession:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def execute(self, statement: object) -> _FakeResult:
        return _FakeResult(self._rows)


def _row(
    geometry: Any,
    *,
    dataset_id: str = "121199",
    resource_version: str = "20220915",
    archive_sha256: str = "a" * 64,
    provenance: ProvenanceV1 | None = None,
) -> dict[str, Any]:
    return {
        "district_id": "A",
        "district_name": "中正區",
        "dataset_id": dataset_id,
        "resource_version": resource_version,
        "archive_sha256": archive_sha256,
        "data_class": ADMINISTRATIVE_DATA_CLASS,
        "classification": DISTRICT_CLASSIFICATION,
        "provenance": (provenance or _provenance()).model_dump(mode="json"),
        "geometry": json.dumps(geometry),
    }


def _list(rows: list[dict[str, Any]]) -> AdministrativeDistrictResponse:
    return list_administrative_districts(cast(Session, _FakeSession(rows)), dataset_id="121199")


def test_application_returns_valid_single_group() -> None:
    response = _list([_row(VALID_GEOMETRY)])
    assert response.data_state == "available"
    assert len(response.features) == 1
    assert response.features[0].geometry.type == "Polygon"


def test_application_accepts_valid_multipolygon() -> None:
    response = _list([_row(VALID_MULTIPOLYGON)])
    assert response.features[0].geometry.type == "MultiPolygon"


def test_application_empty_table_is_empty_state() -> None:
    response = _list([])
    assert response.data_state == "empty"
    assert response.features == []


def test_application_rejects_rows_from_another_dataset() -> None:
    with pytest.raises(AdministrativeDistrictDataError, match="multiple source groups"):
        _list([_row(VALID_GEOMETRY, dataset_id="999999")])


def test_application_rejects_mixed_datasets() -> None:
    with pytest.raises(AdministrativeDistrictDataError, match="multiple source groups"):
        _list([_row(VALID_GEOMETRY), _row(VALID_GEOMETRY, dataset_id="999999")])


def test_application_rejects_mixed_versions() -> None:
    with pytest.raises(AdministrativeDistrictDataError, match="multiple source groups"):
        _list(
            [
                _row(VALID_GEOMETRY, resource_version="20220915"),
                _row(VALID_GEOMETRY, resource_version="20220916"),
            ]
        )


def test_application_rejects_mixed_archive_hashes() -> None:
    with pytest.raises(AdministrativeDistrictDataError, match="multiple source groups"):
        _list([_row(VALID_GEOMETRY), _row(VALID_GEOMETRY, archive_sha256="b" * 64)])


def test_application_rejects_mixed_provenance() -> None:
    other = _provenance().model_copy(update={"attribution": "Other agency"})
    with pytest.raises(AdministrativeDistrictDataError, match="multiple source groups"):
        _list([_row(VALID_GEOMETRY), _row(VALID_GEOMETRY, provenance=other)])


MALFORMED_GEOMETRIES: list[Any] = [
    {"type": "Polygon", "coordinates": "not-a-list"},
    {"type": "Polygon", "coordinates": []},
    {"type": "Polygon", "coordinates": [[[121.5, 25.0], [121.52, 25.0], [121.52, 25.02]]]},
    {
        "type": "Polygon",
        "coordinates": [[["x", 25.0], [121.52, 25.0], [121.52, 25.02], ["x", 25.0]]],
    },
    {
        "type": "Polygon",
        "coordinates": [
            [[121.5, 25.0], [121.52, 25.0], [121.52, 25.02], [float("nan"), 25.0], [121.5, 25.0]]
        ],
    },
    {
        "type": "Polygon",
        "coordinates": [
            [[121.5, 25.0], [121.52, 25.0], [121.52, 25.02], [float("inf"), 25.0], [121.5, 25.0]]
        ],
    },
    {
        "type": "Polygon",
        "coordinates": [
            [
                [121.50, 25.00],
                [121.52, 25.02],
                [121.52, 25.00],
                [121.50, 25.02],
                [121.50, 25.00],
            ]
        ],
    },
    {
        "type": "Polygon",
        "coordinates": [[[10.0, 10.0], [10.02, 10.0], [10.02, 10.02], [10.0, 10.02], [10.0, 10.0]]],
    },
    {"type": "Point", "coordinates": [121.5, 25.0]},
    {"type": "MultiPolygon", "coordinates": [[[[121.5, 25.0], [121.52, 25.0], [121.52, 25.02]]]]},
]


@pytest.mark.parametrize("geometry", MALFORMED_GEOMETRIES)
def test_application_rejects_malformed_persisted_geometry(geometry: Any) -> None:
    with pytest.raises(AdministrativeDistrictDataError, match="geometry is invalid"):
        _list([_row(geometry)])


@pytest.mark.asyncio
async def test_route_rejects_malformed_persisted_geometry_with_500(client: AsyncClient) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession([_row(MALFORMED_GEOMETRIES[1])])
    response = await client.get(ENDPOINT)
    assert response.status_code == 500
    assert response.json() == {"detail": route_module.INVALID_DATA_DETAIL}


@pytest.mark.asyncio
async def test_route_serves_persisted_rows_without_application_monkeypatch(
    client: AsyncClient,
) -> None:
    app.dependency_overrides[get_session] = lambda: _FakeSession([_row(VALID_GEOMETRY)])
    response = await client.get(ENDPOINT)
    assert response.status_code == 200
    payload = response.json()
    assert payload["data_state"] == "available"
    assert payload["provenance"]["schema_version"] == "1"
    assert payload["features"][0]["properties"]["district_name"] == "中正區"
