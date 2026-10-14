from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Classification = Literal["OBSERVED", "INFERRED", "SIMULATED", "UNVERIFIED"]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


class DatabaseStatus(BaseModel):
    status: Literal["available", "unavailable"]
    postgis_version: str | None = None


class SystemStatusResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    database: DatabaseStatus


class LayerResponse(BaseModel):
    id: str
    label: str
    available: bool
    classification: Classification | None
    message: str


class ModelCatalogItem(BaseModel):
    id: str
    version: str
    status: Literal["demonstration"]
    classification: Literal["SIMULATED"]
    description: str


class SimulationPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    study_area: Literal["taipei_synthetic_demo"] = "taipei_synthetic_demo"
    duration_steps: int = Field(default=12, ge=1, le=100)
    walkers: int = Field(default=24, ge=1, le=1000)
    random_seed: int = Field(default=42, ge=0, le=18_446_744_073_709_551_615)
    movement_model: Literal["weighted_random_walk"] = "weighted_random_walk"
    intervention_scenario: Literal["baseline"] = "baseline"


class PreviewParameters(BaseModel):
    study_area: str
    duration_steps: int
    walkers: int
    random_seed: int
    movement_model: str
    intervention_scenario: str


class SimulationProvenance(BaseModel):
    classification: Literal["SIMULATED"]
    source_type: Literal["synthetic_fixture"]
    source_id: str
    source_crs: Literal["EPSG:4326"]
    note: str


class NodeVisit(BaseModel):
    id: str
    coordinates: tuple[float, float]
    visits: int
    probability: float
    classification: Literal["SIMULATED"]


class EdgeVisit(BaseModel):
    source: str
    target: str
    edge_id: str
    movement_weight: float
    visits: int
    probability: float
    classification: Literal["SIMULATED"]


class SimulationPreviewResponse(BaseModel):
    simulation_status: Literal["completed"]
    classification: Literal["SIMULATED"]
    model_id: str
    model_version: str
    parameters: PreviewParameters
    provenance: SimulationProvenance
    assumptions: list[str]
    nodes: list[NodeVisit]
    edges: list[EdgeVisit]
