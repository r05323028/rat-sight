"""Read stormwater infrastructure reference pipelines as bounded GeoJSON.

The endpoint serves the latest version of one explicit dataset. Persisted
geometry is deep-validated before serialization, and an empty viewport result is
distinguished from empty storage via the top-level provenance.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError
from ratsight_api.api.schemas import (
    StormwaterFeature,
    StormwaterLineString,
    StormwaterProperties,
    StormwaterProvenanceV1,
    StormwaterResponse,
)
from ratsight_api.domain.stormwater import (
    BBOX_MAX_SPAN,
    FEATURE_CAP,
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    STORMWATER_CLASSIFICATION,
    STORMWATER_DATA_CLASS,
)
from ratsight_api.infrastructure.config import get_settings
from ratsight_api.infrastructure.database.models import StormwaterPipeline
from shapely.geometry import shape as shapely_shape
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

INVALID_GEOMETRY_MESSAGE = "stored stormwater geometry is invalid"


class StormwaterQueryError(ValueError):
    """Raised when a bbox query parameter is malformed or out of bounds."""


class StormwaterStorageError(RuntimeError):
    """Raised when the database cannot serve the stormwater layer."""


class StormwaterDataError(RuntimeError):
    """Raised when persisted data violates the stormwater contract."""


def parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    """Parse and bound-check ``minX,minY,maxX,maxY`` in EPSG:4326."""
    if value is None:
        return None
    parts = value.split(",")
    if len(parts) != 4:
        raise StormwaterQueryError("bbox must have exactly four minX,minY,maxX,maxY numbers")
    try:
        min_x, min_y, max_x, max_y = (float(part) for part in parts)
    except ValueError as exc:
        raise StormwaterQueryError("bbox values must be numbers") from exc
    if not all(math.isfinite(number) for number in (min_x, min_y, max_x, max_y)):
        raise StormwaterQueryError("bbox values must be finite")
    if not (LON_MIN <= min_x <= LON_MAX and LON_MIN <= max_x <= LON_MAX):
        raise StormwaterQueryError(f"bbox longitude must be within [{LON_MIN}, {LON_MAX}]")
    if not (LAT_MIN <= min_y <= LAT_MAX and LAT_MIN <= max_y <= LAT_MAX):
        raise StormwaterQueryError(f"bbox latitude must be within [{LAT_MIN}, {LAT_MAX}]")
    if min_x > max_x or min_y > max_y:
        raise StormwaterQueryError("bbox must be ordered minX,minY,maxX,maxY")
    if (max_x - min_x) > BBOX_MAX_SPAN or (max_y - min_y) > BBOX_MAX_SPAN:
        raise StormwaterQueryError(f"bbox width and height must not exceed {BBOX_MAX_SPAN} degrees")
    return (min_x, min_y, max_x, max_y)


def _parse_geometry(payload: Any) -> StormwaterLineString:
    if isinstance(payload, (str, bytes)):
        try:
            payload = json.loads(payload)
        except ValueError as exc:
            raise StormwaterDataError(INVALID_GEOMETRY_MESSAGE) from exc
    if not isinstance(payload, Mapping) or payload.get("type") != "LineString":
        raise StormwaterDataError(INVALID_GEOMETRY_MESSAGE)
    coordinates = payload.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise StormwaterDataError(INVALID_GEOMETRY_MESSAGE)
    positions: list[list[float]] = []
    for position in coordinates:
        if not isinstance(position, list) or len(position) != 2:
            raise StormwaterDataError(INVALID_GEOMETRY_MESSAGE)
        x, y = position
        if (
            not isinstance(x, (int, float))
            or isinstance(x, bool)
            or not isinstance(y, (int, float))
            or isinstance(y, bool)
            or not math.isfinite(x)
            or not math.isfinite(y)
        ):
            raise StormwaterDataError(INVALID_GEOMETRY_MESSAGE)
        positions.append([float(x), float(y)])
    if len({(x, y) for x, y in positions}) < 2:
        raise StormwaterDataError(INVALID_GEOMETRY_MESSAGE)
    try:
        geometry = shapely_shape({"type": "LineString", "coordinates": positions})
    except Exception as exc:  # noqa: BLE001 - shapely raises several parse errors
        raise StormwaterDataError(INVALID_GEOMETRY_MESSAGE) from exc
    if geometry.is_empty or not geometry.is_valid:
        raise StormwaterDataError(INVALID_GEOMETRY_MESSAGE)
    return StormwaterLineString(type="LineString", coordinates=positions)


def _empty_response(bbox: tuple[float, float, float, float] | None) -> StormwaterResponse:
    return StormwaterResponse(
        features=[],
        data_state="empty",
        provenance=None,
        feature_count=0,
        bbox=bbox,
        truncated=False,
    )


def list_stormwater_pipelines(
    session: Session,
    *,
    bbox: tuple[float, float, float, float] | None = None,
    dataset_id: str | None = None,
) -> StormwaterResponse:
    """Return the latest version of one explicit dataset, optionally bbox-bounded."""
    resolved_dataset_id = dataset_id or get_settings().stormwater_dataset_id
    columns = (
        StormwaterPipeline.source_record_id,
        StormwaterPipeline.dataset_id,
        StormwaterPipeline.resource_version,
        StormwaterPipeline.archive_sha256,
        StormwaterPipeline.provenance,
        StormwaterPipeline.category_code,
        StormwaterPipeline.pipe_number,
        StormwaterPipeline.start_node_id,
        StormwaterPipeline.end_node_id,
        StormwaterPipeline.managing_unit,
        StormwaterPipeline.work_category,
        StormwaterPipeline.installation_date,
        StormwaterPipeline.dimension_unit,
        StormwaterPipeline.diameter_width,
        StormwaterPipeline.diameter_height,
        StormwaterPipeline.conduit_count,
        StormwaterPipeline.material,
        StormwaterPipeline.start_burial_depth,
        StormwaterPipeline.end_burial_depth,
        StormwaterPipeline.length,
        StormwaterPipeline.pipe_type,
        StormwaterPipeline.use_status,
        StormwaterPipeline.data_status,
        StormwaterPipeline.notes,
        func.ST_AsGeoJSON(StormwaterPipeline.geometry).label("geometry"),
    )
    try:
        meta = (
            session.execute(
                select(
                    StormwaterPipeline.resource_version,
                    StormwaterPipeline.archive_sha256,
                    StormwaterPipeline.provenance,
                )
                .where(StormwaterPipeline.dataset_id == resolved_dataset_id)
                .order_by(StormwaterPipeline.resource_version.desc())
                .limit(1)
            )
            .mappings()
            .first()
        )
    except SQLAlchemyError as exc:
        raise StormwaterStorageError("stormwater storage unavailable") from exc
    if meta is None:
        return _empty_response(bbox)

    try:
        provenance = StormwaterProvenanceV1.model_validate(meta["provenance"])
    except ValidationError as exc:
        raise StormwaterDataError("stored stormwater provenance failed validation") from exc

    statement = (
        select(*columns)
        .where(StormwaterPipeline.dataset_id == resolved_dataset_id)
        .where(StormwaterPipeline.resource_version == meta["resource_version"])
        .order_by(StormwaterPipeline.source_record_id)
        .limit(FEATURE_CAP + 1)
    )
    if bbox is not None:
        min_x, min_y, max_x, max_y = bbox
        statement = statement.where(
            func.ST_Intersects(
                StormwaterPipeline.geometry,
                func.ST_MakeEnvelope(min_x, min_y, max_x, max_y, 4326),
            )
        )
    try:
        rows = session.execute(statement).mappings().all()
    except SQLAlchemyError as exc:
        raise StormwaterStorageError("stormwater storage unavailable") from exc

    truncated = len(rows) > FEATURE_CAP
    rows = rows[:FEATURE_CAP]

    features: list[StormwaterFeature] = []
    for row in rows:
        if (
            row["dataset_id"] != resolved_dataset_id
            or row["resource_version"] != meta["resource_version"]
            or row["archive_sha256"] != meta["archive_sha256"]
        ):
            raise StormwaterDataError("persisted stormwater rows span multiple source groups")
        attribute_values = {
            name: row[name]
            for name in (
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
            )
        }
        features.append(
            StormwaterFeature(
                id=row["source_record_id"],
                geometry=_parse_geometry(row["geometry"]),
                properties=StormwaterProperties(
                    segment_id=row["source_record_id"],
                    data_class=STORMWATER_DATA_CLASS,
                    classification=STORMWATER_CLASSIFICATION,
                    provenance_schema_version=provenance.schema_version,
                    dataset_id=row["dataset_id"],
                    resource_version=row["resource_version"],
                    archive_sha256=row["archive_sha256"],
                    **attribute_values,
                ),
            )
        )

    return StormwaterResponse(
        features=features,
        data_state="available",
        provenance=provenance,
        feature_count=len(features),
        bbox=bbox,
        truncated=truncated,
    )
