"""Read administrative reference districts as an honest GeoJSON envelope.

The canonical provenance object is stored per row and serialized once at the
response top level. Feature properties reference provenance by schema version
and source identity but never duplicate the full object.

The endpoint serves one explicit dataset identity and one dataset-version pair.
Rows that span multiple datasets, versions, archive hashes, or provenance
objects are rejected as invalid persisted data rather than silently mixed.
Persisted geometry is deep-validated before serialization so malformed records
surface as an explicit server error instead of invalid GeoJSON.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import ValidationError
from ratsight_api.api.schemas import (
    AdministrativeDistrictFeature,
    AdministrativeDistrictProperties,
    AdministrativeDistrictResponse,
    GeoJsonGeometry,
    ProvenanceV1,
)
from ratsight_api.domain.administrative_districts import (
    ADMINISTRATIVE_DATA_CLASS,
    DISTRICT_CLASSIFICATION,
    TARGET_ENVELOPE,
)
from ratsight_api.infrastructure.config import get_settings
from ratsight_api.infrastructure.database.models import AdministrativeDistrict
from shapely.geometry import shape as shapely_shape
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

INVALID_GEOMETRY_MESSAGE = "stored administrative district geometry is invalid"
MIXED_GROUP_MESSAGE = "persisted administrative district rows span multiple source groups"


class AdministrativeDistrictStorageError(RuntimeError):
    """Raised when the database cannot serve the administrative district layer."""


class AdministrativeDistrictDataError(RuntimeError):
    """Raised when persisted data violates the administrative district contract."""


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _validate_ring(ring: Any) -> None:
    if not isinstance(ring, Sequence) or isinstance(ring, (str, bytes)) or len(ring) < 4:
        raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)
    positions: list[tuple[float, float]] = []
    for position in ring:
        if (
            not isinstance(position, Sequence)
            or isinstance(position, (str, bytes))
            or len(position) != 2
        ):
            raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)
        x, y = position
        if not _is_finite_number(x) or not _is_finite_number(y):
            raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)
        positions.append((float(x), float(y)))
    if positions[0] != positions[-1]:
        raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)


def _validate_polygon_rings(rings: Any) -> None:
    if not isinstance(rings, Sequence) or isinstance(rings, (str, bytes)) or not rings:
        raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)
    for ring in rings:
        _validate_ring(ring)


def _validate_geometry_coordinates(geometry_type: Any, coordinates: Any) -> None:
    if geometry_type == "Polygon":
        _validate_polygon_rings(coordinates)
        return
    if geometry_type == "MultiPolygon":
        if (
            not isinstance(coordinates, Sequence)
            or isinstance(coordinates, (str, bytes))
            or not coordinates
        ):
            raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)
        for polygon in coordinates:
            _validate_polygon_rings(polygon)
        return
    raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)


def _parse_geometry(payload: Any) -> GeoJsonGeometry:
    """Validate persisted GeoJSON structure, coordinates, and geometry validity."""
    if isinstance(payload, (str, bytes)):
        try:
            payload = json.loads(payload)
        except ValueError as exc:
            raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE) from exc
    if not isinstance(payload, Mapping):
        raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)
    geometry_type = payload.get("type")
    coordinates: Any = payload.get("coordinates")
    if geometry_type not in {"Polygon", "MultiPolygon"}:
        raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)
    _validate_geometry_coordinates(geometry_type, coordinates)
    try:
        geometry = shapely_shape({"type": geometry_type, "coordinates": coordinates})
    except Exception as exc:  # noqa: BLE001 - shapely raises several parse errors
        raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE) from exc
    if geometry.is_empty or not geometry.is_valid:
        raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)
    min_x, min_y, max_x, max_y = geometry.bounds
    if not all(math.isfinite(value) for value in (min_x, min_y, max_x, max_y)):
        raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)
    env_min_x, env_min_y, env_max_x, env_max_y = TARGET_ENVELOPE
    if not (
        env_min_x <= min_x and env_min_y <= min_y and max_x <= env_max_x and max_y <= env_max_y
    ):
        raise AdministrativeDistrictDataError(INVALID_GEOMETRY_MESSAGE)
    return GeoJsonGeometry(type=geometry_type, coordinates=list(coordinates))


def _empty_response() -> AdministrativeDistrictResponse:
    return AdministrativeDistrictResponse(features=[], data_state="empty", provenance=None)


def _assemble_response(
    rows: Sequence[Any],
    *,
    dataset_id: str,
) -> AdministrativeDistrictResponse:
    if not rows:
        return _empty_response()

    dataset_ids = {row["dataset_id"] for row in rows}
    resource_versions = {row["resource_version"] for row in rows}
    archive_hashes = {row["archive_sha256"] for row in rows}
    if dataset_ids != {dataset_id} or len(resource_versions) != 1 or len(archive_hashes) != 1:
        raise AdministrativeDistrictDataError(MIXED_GROUP_MESSAGE)

    first_provenance = rows[0]["provenance"]
    try:
        provenance = ProvenanceV1.model_validate(first_provenance)
    except ValidationError as exc:
        raise AdministrativeDistrictDataError("stored provenance failed validation") from exc
    if any(row["provenance"] != first_provenance for row in rows):
        raise AdministrativeDistrictDataError(MIXED_GROUP_MESSAGE)

    features: list[AdministrativeDistrictFeature] = []
    for row in rows:
        if (
            row["data_class"] != ADMINISTRATIVE_DATA_CLASS
            or row["classification"] != DISTRICT_CLASSIFICATION
        ):
            raise AdministrativeDistrictDataError("stored data_class/classification is invalid")
        features.append(
            AdministrativeDistrictFeature(
                id=row["district_id"],
                properties=AdministrativeDistrictProperties(
                    district_id=row["district_id"],
                    district_name=row["district_name"],
                    data_class=ADMINISTRATIVE_DATA_CLASS,
                    classification=DISTRICT_CLASSIFICATION,
                    provenance_schema_version=provenance.schema_version,
                    dataset_id=row["dataset_id"],
                    resource_version=row["resource_version"],
                    archive_sha256=row["archive_sha256"],
                ),
                geometry=_parse_geometry(row["geometry"]),
            )
        )

    return AdministrativeDistrictResponse(
        features=features,
        data_state="available",
        provenance=provenance,
    )


def list_administrative_districts(
    session: Session,
    *,
    dataset_id: str | None = None,
) -> AdministrativeDistrictResponse:
    """Return the latest version of one explicit dataset, or an explicit empty state."""
    resolved_dataset_id = dataset_id or get_settings().administrative_district_dataset_id
    latest_version = (
        select(func.max(AdministrativeDistrict.resource_version))
        .where(AdministrativeDistrict.dataset_id == resolved_dataset_id)
        .scalar_subquery()
    )
    statement = (
        select(
            AdministrativeDistrict.district_id,
            AdministrativeDistrict.district_name,
            AdministrativeDistrict.dataset_id,
            AdministrativeDistrict.resource_version,
            AdministrativeDistrict.archive_sha256,
            AdministrativeDistrict.data_class,
            AdministrativeDistrict.classification,
            AdministrativeDistrict.provenance,
            func.ST_AsGeoJSON(AdministrativeDistrict.geometry).label("geometry"),
        )
        .where(AdministrativeDistrict.dataset_id == resolved_dataset_id)
        .where(AdministrativeDistrict.resource_version == latest_version)
        .order_by(AdministrativeDistrict.district_id)
    )
    try:
        rows = session.execute(statement).mappings().all()
    except SQLAlchemyError as exc:
        raise AdministrativeDistrictStorageError(
            "administrative district storage unavailable"
        ) from exc

    return _assemble_response(rows, dataset_id=resolved_dataset_id)
