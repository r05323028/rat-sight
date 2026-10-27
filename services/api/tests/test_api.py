from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from ratsight_api.application.citizen_report_aggregates import (
    CitizenReportDatasetUnknown,
    CitizenReportOriginIneligible,
    CitizenReportSourceVersionConflict,
)
from ratsight_api.main import app
from ratsight_simulation.graph.network import create_synthetic_graph

ORIGIN_SOURCE = {
    "dataset_id": "ratdar-taipei-public-export",
    "resource_version": "2026-10-26T20:53:32Z",
    "content_sha256": "e" * 64,
}
OSM_CELL_ORIGIN = {
    "study_area": "taipei_osm_songshan",
    "origin_cell_id": "g250m:11143:49036:2026-05:sighting",
    "origin_source": ORIGIN_SOURCE,
}


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ratsight-api"}


@pytest.mark.asyncio
async def test_openapi_contains_required_routes(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    assert "/api/v1/simulations/preview" in schema["paths"]
    assert "/api/v1/layers" in schema["paths"]
    assert "/api/v1/system/status" in schema["paths"]
    assert "/api/v1/rodent-reports" not in schema["paths"]
    request = schema["components"]["schemas"]["SimulationPreviewRequest"]
    assert request["allOf"][0]["then"]["required"] == ["origin_cell_id", "origin_source"]
    assert request["allOf"][0]["then"]["not"]["required"] == ["origin_node_id"]
    assert request["allOf"][1]["then"]["anyOf"] == [
        {"required": ["origin_node_id"]},
        {"required": ["origin_cell_id"]},
    ]


@pytest.mark.asyncio
async def test_layers_are_explicitly_empty_not_fake_data(client: AsyncClient) -> None:
    response = await client.get("/api/v1/layers")
    assert response.status_code == 200
    layers = response.json()
    assert len(layers) == 6
    assert all(layer["available"] is False for layer in layers)
    assert all(layer["classification"] is None for layer in layers[:-1])


@pytest.mark.asyncio
async def test_models_catalog_marks_preview_as_demo(client: AsyncClient) -> None:
    models = (await client.get("/api/v1/simulations/models")).json()
    assert len(models) == 1
    assert models[0]["status"] == "demonstration"
    assert models[0]["classification"] == "SIMULATED"


@pytest.mark.asyncio
async def test_preview_is_deterministic_and_carries_provenance(
    client: AsyncClient,
) -> None:
    payload = {
        "study_area": "taipei_synthetic_demo",
        "walkers": 12,
        "duration_steps": 6,
        "random_seed": 99,
        "origin_node_id": "n0",
    }
    first = await client.post("/api/v1/simulations/preview", json=payload)
    second = await client.post("/api/v1/simulations/preview", json=payload)
    assert first.status_code == 200
    result = first.json()
    assert result == second.json()
    assert result["classification"] == "SIMULATED"
    assert result["model_id"] == "synthetic_weighted_random_walk"
    assert result["parameters"]["random_seed"] == 99
    assert result["provenance"]["source_type"] == "synthetic_fixture"
    assert result["assumptions"]
    assert sum(node["probability"] for node in result["nodes"]) == pytest.approx(1.0)
    assert sum(edge["probability"] for edge in result["edges"]) == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_preview_requires_explicit_study_area(client: AsyncClient) -> None:
    response = await client.post("/api/v1/simulations/preview", json={})

    assert response.status_code == 422
    assert any(error["loc"][-1] == "study_area" for error in response.json()["detail"])


@pytest.mark.asyncio
async def test_osm_preview_requires_a_citizen_cell_origin(client: AsyncClient) -> None:
    missing = await client.post(
        "/api/v1/simulations/preview", json={"study_area": "taipei_osm_songshan"}
    )
    graph_node = await client.post(
        "/api/v1/simulations/preview",
        json={"study_area": "taipei_osm_songshan", "origin_node_id": "n0"},
    )
    unversioned = await client.post(
        "/api/v1/simulations/preview",
        json={
            "study_area": "taipei_osm_songshan",
            "origin_cell_id": "g250m:11143:49036:2026-05:sighting",
        },
    )

    assert missing.status_code == 422
    assert "origin_cell_id is required" in missing.text
    assert graph_node.status_code == 422
    assert "origin_node_id is not accepted" in graph_node.text
    assert unversioned.status_code == 422
    assert "origin_source" in unversioned.text


@pytest.mark.asyncio
async def test_preview_reports_a_missing_osm_source_instead_of_falling_back(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_source() -> None:
        raise FileNotFoundError(
            "configured OSM source is absent: /nonexistent/taipei-expanded-ratdar-20261027.osm"
        )

    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.load_osm_surface_graph",
        missing_source,
    )
    response = await client.post("/api/v1/simulations/preview", json=OSM_CELL_ORIGIN)

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["code"] == "SOURCE_NETWORK_UNAVAILABLE"
    assert detail["provisioning"]


@pytest.mark.asyncio
async def test_preview_rejects_unknown_fields_and_invalid_duration(
    client: AsyncClient,
) -> None:
    extra_field = await client.post("/api/v1/simulations/preview", json={"extra": True})
    invalid_duration = await client.post(
        "/api/v1/simulations/preview",
        json={"duration_steps": 0},
    )
    assert extra_field.status_code == 422
    assert invalid_duration.status_code == 422


def _stub_osm_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep route error tests off the expanded extract while preserving the flow."""

    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.load_osm_surface_graph",
        create_synthetic_graph,
    )


@pytest.mark.asyncio
async def test_preview_maps_a_source_version_conflict_to_409(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def stale_source(*_args: object, **_kwargs: object) -> None:
        raise CitizenReportSourceVersionConflict("requested snapshot is not the current one")

    _stub_osm_graph(monkeypatch)
    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.get_citizen_report_origin_cell",
        stale_source,
    )
    response = await client.post("/api/v1/simulations/preview", json=OSM_CELL_ORIGIN)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "ORIGIN_SOURCE_VERSION_CONFLICT"
    assert detail["action"] == "Refresh citizen reports and select an origin again."
    assert detail["dataset_id"] == ORIGIN_SOURCE["dataset_id"]
    assert detail["resource_version"] == ORIGIN_SOURCE["resource_version"]
    assert "251" not in response.text


@pytest.mark.asyncio
async def test_preview_rejects_a_context_only_report_category(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def ineligible(*_args: object, **_kwargs: object) -> None:
        raise CitizenReportOriginIneligible("context_only_bait_station")

    _stub_osm_graph(monkeypatch)
    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.get_citizen_report_origin_cell",
        ineligible,
    )
    payload = {
        "study_area": "taipei_osm_songshan",
        "origin_cell_id": "g250m:11143:49036:2026-05:bait_station",
        "origin_source": ORIGIN_SOURCE,
    }
    response = await client.post("/api/v1/simulations/preview", json=payload)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "ORIGIN_REPORT_TYPE_INELIGIBLE"
    assert detail["reason"] == "context_only_bait_station"
    assert detail["report_type"] == "bait_station"
    assert detail["classification"] == "UNVERIFIED"
    assert detail["policy_version"] == "origin-report-category-v1"
    assert "無法作為模擬起點" in detail["message"]


@pytest.mark.asyncio
async def test_preview_rejects_an_unknown_report_dataset(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unknown(*_args: object, **_kwargs: object) -> None:
        raise CitizenReportDatasetUnknown("no published snapshot for dataset")

    _stub_osm_graph(monkeypatch)
    monkeypatch.setattr(
        "ratsight_api.application.simulation_preview.get_citizen_report_origin_cell",
        unknown,
    )
    response = await client.post("/api/v1/simulations/preview", json=OSM_CELL_ORIGIN)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "ORIGIN_SOURCE_UNKNOWN"
    assert detail["dataset_id"] == ORIGIN_SOURCE["dataset_id"]
