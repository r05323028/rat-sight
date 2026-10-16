from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_serializer

Classification = Literal["OBSERVED", "INFERRED", "SIMULATED", "UNVERIFIED"]
DataClass = Literal["ADMINISTRATIVE_REFERENCE"]
InfrastructureDataClass = Literal["INFRASTRUCTURE_REFERENCE"]
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


# --- Stormwater infrastructure reference pipelines ---------------------------
# Stormwater geometry is infrastructure reference data. ``data_class`` stays a
# separate axis from epistemic ``classification``; endpoint IDs are publisher
# attributes, never topology.


def _validate_http_url(value: str) -> str:
    if not value.startswith(("http://", "https://")):
        raise ValueError("must be an http(s) URI")
    return value


def _validate_sha256(value: str) -> str:
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("must be 64 lowercase hex characters")
    return value


def _validate_rfc3339_utc(value: str) -> str:
    if not value.endswith("Z"):
        raise ValueError("must be an RFC3339 UTC timestamp ending in Z")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("must be a valid RFC3339 timestamp") from exc
    return value


def _validate_uuid(value: str) -> str:
    try:
        uuid.UUID(value)
    except ValueError as exc:
        raise ValueError("must be a UUID string") from exc
    return value


class StormwaterProcessing(BaseModel):
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


class StormwaterSourceQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_only: bool
    missing_pipe_number_count: int = Field(ge=0)
    duplicate_pipe_number_value_count: int = Field(ge=0)
    missing_start_endpoint_count: int = Field(ge=0)
    missing_end_endpoint_count: int = Field(ge=0)
    missing_notes_count: int = Field(ge=0)


class StormwaterUncertainty(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currentness: str = Field(min_length=1)
    note: str = Field(min_length=1)


class StormwaterProvenanceV1(BaseModel):
    """Immutable version-1 provenance object for the stormwater reference layer."""

    model_config = ConfigDict(extra="forbid")

    schema_version: ProvenanceSchemaVersion = "1"
    source_url: str
    download_url: str
    dataset_id: str
    resource_id: str
    resource_version: str
    retrieved_at: str
    archive_sha256: str
    license: str = Field(min_length=1)
    attribution: str = Field(min_length=1)
    source_crs: Literal["EPSG:3826"] = "EPSG:3826"
    target_crs: Literal["EPSG:4326"] = "EPSG:4326"
    z_handling: Literal["dropped", "retained", "not_present"]
    processing: StormwaterProcessing
    source_quality: StormwaterSourceQuality
    uncertainty: StormwaterUncertainty

    @field_validator("source_url", "download_url")
    @classmethod
    def _url(cls, value: str) -> str:
        return _validate_http_url(value)

    @field_validator("dataset_id", "resource_id")
    @classmethod
    def _identity_uuid(cls, value: str) -> str:
        return _validate_uuid(value)

    @field_validator("resource_version", "retrieved_at")
    @classmethod
    def _timestamps(cls, value: str) -> str:
        return _validate_rfc3339_utc(value)

    @field_validator("archive_sha256")
    @classmethod
    def _hash(cls, value: str) -> str:
        return _validate_sha256(value)


class StormwaterProperties(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_id: str = Field(min_length=1)
    data_class: InfrastructureDataClass
    classification: Literal["UNVERIFIED"]
    provenance_schema_version: ProvenanceSchemaVersion
    dataset_id: str
    resource_version: str
    archive_sha256: str
    category_code: str | None = None
    pipe_number: str | None = None
    start_node_id: str | None = None
    end_node_id: str | None = None
    managing_unit: str | None = None
    work_category: str | None = None
    installation_date: str | None = None
    dimension_unit: str | None = None
    diameter_width: str | None = None
    diameter_height: str | None = None
    conduit_count: str | None = None
    material: str | None = None
    start_burial_depth: str | None = None
    end_burial_depth: str | None = None
    length: str | None = None
    pipe_type: str | None = None
    use_status: str | None = None
    data_status: str | None = None
    notes: str | None = None

    @model_serializer(mode="wrap")
    def _omit_null_attributes(self, handler: Any) -> dict[str, Any]:
        data: dict[str, Any] = handler(self)
        return {key: value for key, value in data.items() if value is not None}


class StormwaterLineString(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[list[float]]

    @field_validator("coordinates")
    @classmethod
    def _has_two_positions(cls, value: list[list[float]]) -> list[list[float]]:
        if len(value) < 2 or any(len(position) != 2 for position in value):
            raise ValueError("LineString requires at least two [lon, lat] positions")
        return value


class StormwaterFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    id: str
    geometry: StormwaterLineString
    properties: StormwaterProperties


class StormwaterResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[StormwaterFeature]
    data_state: Literal["empty", "available"]
    data_class: InfrastructureDataClass = "INFRASTRUCTURE_REFERENCE"
    provenance: StormwaterProvenanceV1 | None = None
    feature_count: int = Field(ge=0)
    bbox: tuple[float, float, float, float] | None = None
    truncated: bool = False
