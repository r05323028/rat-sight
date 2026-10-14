from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from ratsight_api.main import app


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


@pytest.mark.asyncio
async def test_layers_are_explicitly_empty_not_fake_data(client: AsyncClient) -> None:
    response = await client.get("/api/v1/layers")
    assert response.status_code == 200
    layers = response.json()
    assert len(layers) == 7
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
    payload = {"walkers": 12, "duration_steps": 6, "random_seed": 99}
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
