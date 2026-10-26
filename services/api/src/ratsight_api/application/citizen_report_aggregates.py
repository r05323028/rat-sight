"""Read suppressed 250 m citizen-report aggregates as bounded GeoJSON.

Rows are UNVERIFIED counts of third-party citizen reports, never observations,
prevalence, population, movement, or disease-risk evidence. Only the latest
imported resource version is served, and only cells that reached the
suppression minimum exist in storage.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError
from ratsight_api.api.schemas import (
    CitizenReportAggregateResponse,
    CitizenReportCellFeature,
    CitizenReportCellPolygon,
    CitizenReportCellProperties,
    CitizenReportProvenanceV1,
)
from ratsight_api.domain.citizen_report_aggregates import (
    ATTRIBUTION,
    BBOX_MAX_SPAN,
    CITIZEN_REPORT_CLASSIFICATION,
    CITIZEN_REPORT_DATA_CLASS,
    DATASET_ID,
    FEATURE_CAP,
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    MONTH_PATTERN,
    NOTICE,
)
from ratsight_api.infrastructure.database.models import CitizenReportCell
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

INVALID_GEOMETRY_MESSAGE = "stored citizen report cell geometry is invalid"
MONTH_RE = re.compile(MONTH_PATTERN)


class CitizenReportQueryError(ValueError):
    """Raised when a bbox, month, or report-type query parameter is malformed."""


class CitizenReportStorageError(RuntimeError):
    """Raised when the database cannot serve the aggregate layer."""


class CitizenReportDataError(RuntimeError):
    """Raised when persisted aggregates violate the layer contract."""


def parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    parts = value.split(",")
    if len(parts) != 4:
        raise CitizenReportQueryError("bbox must have exactly four minX,minY,maxX,maxY numbers")
    try:
        min_x, min_y, max_x, max_y = (float(part) for part in parts)
    except ValueError as exc:
        raise CitizenReportQueryError("bbox values must be numbers") from exc
    if not all(math.isfinite(number) for number in (min_x, min_y, max_x, max_y)):
        raise CitizenReportQueryError("bbox values must be finite")
    if not (LON_MIN <= min_x <= LON_MAX and LON_MIN <= max_x <= LON_MAX):
        raise CitizenReportQueryError(f"bbox longitude must be within [{LON_MIN}, {LON_MAX}]")
    if not (LAT_MIN <= min_y <= LAT_MAX and LAT_MIN <= max_y <= LAT_MAX):
        raise CitizenReportQueryError(f"bbox latitude must be within [{LAT_MIN}, {LAT_MAX}]")
    if min_x > max_x or min_y > max_y:
        raise CitizenReportQueryError("bbox must be ordered minX,minY,maxX,maxY")
    if (max_x - min_x) > BBOX_MAX_SPAN or (max_y - min_y) > BBOX_MAX_SPAN:
        raise CitizenReportQueryError(
            f"bbox width and height must not exceed {BBOX_MAX_SPAN} degrees"
        )
    return (min_x, min_y, max_x, max_y)


def parse_months(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    months = [part.strip() for part in value.split(",") if part.strip()]
    if not months:
        raise CitizenReportQueryError("months must list at least one YYYY-MM bucket")
    for month in months:
        if MONTH_RE.fullmatch(month) is None:
            raise CitizenReportQueryError(f"month bucket must be YYYY-MM: {month!r}")
    return tuple(sorted(set(months)))


def _parse_polygon(payload: Any) -> CitizenReportCellPolygon:
    if isinstance(payload, (str, bytes)):
        try:
            payload = json.loads(payload)
        except ValueError as exc:
            raise CitizenReportDataError(INVALID_GEOMETRY_MESSAGE) from exc
    if not isinstance(payload, Mapping) or payload.get("type") != "Polygon":
        raise CitizenReportDataError(INVALID_GEOMETRY_MESSAGE)
    coordinates = payload.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise CitizenReportDataError(INVALID_GEOMETRY_MESSAGE)
    for ring in coordinates:
        if not isinstance(ring, list) or len(ring) < 4:
            raise CitizenReportDataError(INVALID_GEOMETRY_MESSAGE)
        for position in ring:
            if (
                not isinstance(position, list)
                or len(position) != 2
                or any(
                    not isinstance(number, (int, float))
                    or isinstance(number, bool)
                    or not math.isfinite(number)
                    for number in position
                )
            ):
                raise CitizenReportDataError(INVALID_GEOMETRY_MESSAGE)
    return CitizenReportCellPolygon(coordinates=coordinates)


def _empty_response(
    bbox: tuple[float, float, float, float] | None,
    months: tuple[str, ...] | None,
) -> CitizenReportAggregateResponse:
    return CitizenReportAggregateResponse(
        features=[],
        data_state="empty",
        notice=NOTICE,
        provenance=None,
        feature_count=0,
        bbox=bbox,
        truncated=False,
    )


def list_citizen_report_aggregates(
    session: Session,
    *,
    bbox: str | None = None,
    months: str | None = None,
    report_type: str | None = None,
    dataset_id: str | None = None,
) -> CitizenReportAggregateResponse:
    """Return suppressed cell counts from the latest imported version."""
    parsed_bbox = parse_bbox(bbox)
    parsed_months = parse_months(months)
    resolved_dataset_id = dataset_id or DATASET_ID
    if report_type is not None and not report_type.strip():
        raise CitizenReportQueryError("report_type must not be empty")

    try:
        meta = (
            session.execute(
                select(CitizenReportCell.resource_version, CitizenReportCell.provenance)
                .where(CitizenReportCell.dataset_id == resolved_dataset_id)
                .order_by(CitizenReportCell.resource_version.desc())
                .limit(1)
            )
            .mappings()
            .first()
        )
    except SQLAlchemyError as exc:
        raise CitizenReportStorageError("citizen report storage unavailable") from exc
    if meta is None:
        return _empty_response(parsed_bbox, parsed_months)

    try:
        CitizenReportProvenanceV1.model_validate(meta["provenance"])
    except ValidationError as exc:
        raise CitizenReportDataError("stored citizen report provenance failed validation") from exc

    statement = (
        select(
            CitizenReportCell.cell_id,
            CitizenReportCell.month,
            CitizenReportCell.report_type,
            CitizenReportCell.report_count,
            CitizenReportCell.data_class,
            CitizenReportCell.classification,
            func.ST_AsGeoJSON(CitizenReportCell.geometry).label("geometry"),
        )
        .where(CitizenReportCell.dataset_id == resolved_dataset_id)
        .where(CitizenReportCell.resource_version == meta["resource_version"])
        .order_by(CitizenReportCell.month, CitizenReportCell.cell_id, CitizenReportCell.report_type)
        .limit(FEATURE_CAP + 1)
    )
    if parsed_bbox is not None:
        min_x, min_y, max_x, max_y = parsed_bbox
        statement = statement.where(
            func.ST_Intersects(
                CitizenReportCell.geometry,
                func.ST_MakeEnvelope(min_x, min_y, max_x, max_y, 4326),
            )
        )
    if parsed_months is not None:
        statement = statement.where(CitizenReportCell.month.in_(parsed_months))
    if report_type is not None:
        statement = statement.where(CitizenReportCell.report_type == report_type.strip())

    try:
        rows = session.execute(statement).mappings().all()
    except SQLAlchemyError as exc:
        raise CitizenReportStorageError("citizen report storage unavailable") from exc

    truncated = len(rows) > FEATURE_CAP
    features: list[CitizenReportCellFeature] = []
    for row in rows[:FEATURE_CAP]:
        if row["data_class"] != CITIZEN_REPORT_DATA_CLASS:
            raise CitizenReportDataError("stored citizen report data_class is invalid")
        if row["classification"] != CITIZEN_REPORT_CLASSIFICATION:
            raise CitizenReportDataError("stored citizen report classification is invalid")
        features.append(
            CitizenReportCellFeature(
                id=f"{row['cell_id']}:{row['month']}:{row['report_type']}",
                geometry=_parse_polygon(row["geometry"]),
                properties=CitizenReportCellProperties(
                    cell_id=row["cell_id"],
                    month=row["month"],
                    report_type=row["report_type"],
                    count=int(row["report_count"]),
                    attribution=ATTRIBUTION,
                ),
            )
        )

    return CitizenReportAggregateResponse(
        features=features,
        data_state="available" if features else "empty",
        notice=NOTICE,
        provenance=CitizenReportProvenanceV1.model_validate(meta["provenance"]),
        feature_count=len(features),
        bbox=parsed_bbox,
        truncated=truncated,
    )
