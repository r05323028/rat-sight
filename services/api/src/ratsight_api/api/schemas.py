from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Classification = Literal["OBSERVED", "INFERRED", "SIMULATED", "UNVERIFIED"]
DataClass = Literal["ADMINISTRATIVE_REFERENCE"]
ProvenanceSchemaVersion = Literal["1"]


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


# --- Administrative reference boundaries -------------------------------------
# Administrative reference geometry is deliberately kept off the epistemic
# `Classification` axis: `data_class` is a separate discriminator and the
# epistemic value is `UNVERIFIED` because source currentness is unresolved.


class ProvenanceProcessing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: str = Field(min_length=1)
    tool_version: str = Field(min_length=1)
    steps: list[str] = Field(min_length=1)

    @field_validator("steps")
    @classmethod
    def _steps_are_non_empty(cls, value: list[str]) -> list[str]:
        if any(not step.strip() for step in value):
            raise ValueError("processing steps must be non-empty strings")
        return value


class ProvenanceUncertainty(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currentness: str = Field(min_length=1)
    note: str = Field(min_length=1)


class ProvenanceV1(BaseModel):
    """Immutable version-1 provenance object for administrative reference data."""

    model_config = ConfigDict(extra="forbid")

    schema_version: ProvenanceSchemaVersion = "1"
    source_url: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    resource_version: str = Field(min_length=1)
    retrieved_at: str = Field(min_length=1)
    archive_sha256: str
    license: str = Field(min_length=1)
    attribution: str = Field(min_length=1)
    source_crs: Literal["EPSG:3826"] = "EPSG:3826"
    target_crs: Literal["EPSG:4326"] = "EPSG:4326"
    processing: ProvenanceProcessing
    uncertainty: ProvenanceUncertainty

    @field_validator("source_url")
    @classmethod
    def _source_url_is_http(cls, value: str) -> str:
        if not value.startswith(("http://", "https://")):
            raise ValueError("source_url must be an http(s) URI")
        return value

    @field_validator("archive_sha256")
    @classmethod
    def _sha256_is_lowercase_hex(cls, value: str) -> str:
        if re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError("archive_sha256 must be 64 lowercase hex characters")
        return value

    @field_validator("retrieved_at")
    @classmethod
    def _retrieved_at_is_rfc3339_utc(cls, value: str) -> str:
        if not value.endswith("Z"):
            raise ValueError("retrieved_at must be an RFC3339 UTC timestamp ending in Z")
        try:
            datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError as exc:  # pragma: no cover - guarded by explicit test
            raise ValueError("retrieved_at must be a valid RFC3339 timestamp") from exc
        return value


class AdministrativeDistrictProperties(BaseModel):
    district_id: str
    district_name: str
    data_class: DataClass
    classification: Literal["UNVERIFIED"]
    provenance_schema_version: ProvenanceSchemaVersion
    dataset_id: str
    resource_version: str
    archive_sha256: str


class GeoJsonGeometry(BaseModel):
    type: Literal["Polygon", "MultiPolygon"]
    coordinates: list[Any]


class AdministrativeDistrictFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    properties: AdministrativeDistrictProperties
    geometry: GeoJsonGeometry


class AdministrativeDistrictResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[AdministrativeDistrictFeature]
    data_state: Literal["empty", "available"]
    data_class: DataClass = "ADMINISTRATIVE_REFERENCE"
    provenance: ProvenanceV1 | None = None
