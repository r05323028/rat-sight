"""Read fixture-only rodent reports as bounded GeoJSON.

Synthetic report-shaped records are SIMULATED report events. The endpoint
distinguishes storage-empty from an in-filter empty result and never exposes
personal or importer-only fields.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from ratsight_api.api.schemas import (
    RodentReportFeature,
    RodentReportPoint,
    RodentReportProperties,
    RodentReportProvenanceV1,
    RodentReportResponse,
)
from ratsight_api.domain.rodent_reports import (
    BBOX_MAX_SPAN,
    FEATURE_CAP,
    LAT_MAX,
    LAT_MIN,
    LON_MAX,
    LON_MIN,
    RODENT_REPORT_CLASSIFICATION,
    RODENT_REPORT_DATA_CLASS,
    SOURCE_KIND,
)
from ratsight_api.importers.rodent_reports import parse_rfc3339_utc
from ratsight_api.infrastructure.config import get_settings
from ratsight_api.infrastructure.database.models import RodentReport
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

INVALID_GEOMETRY_MESSAGE = "stored rodent report geometry is invalid"


class RodentReportQueryError(ValueError):
    """Raised when a bbox or time query parameter is malformed or out of range."""


class RodentReportStorageError(RuntimeError):
    """Raised when the database cannot serve the rodent report layer."""


class RodentReportDataError(RuntimeError):
    """Raised when persisted data violates the rodent report contract."""


def parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    parts = value.split(",")
    if len(parts) != 4:
        raise RodentReportQueryError("bbox must have exactly four minX,minY,maxX,maxY numbers")
    try:
        min_x, min_y, max_x, max_y = (float(part) for part in parts)
    except ValueError as exc:
        raise RodentReportQueryError("bbox values must be numbers") from exc
    if not all(math.isfinite(number) for number in (min_x, min_y, max_x, max_y)):
        raise RodentReportQueryError("bbox values must be finite")
    if not (LON_MIN <= min_x <= LON_MAX and LON_MIN <= max_x <= LON_MAX):
        raise RodentReportQueryError(f"bbox longitude must be within [{LON_MIN}, {LON_MAX}]")
    if not (LAT_MIN <= min_y <= LAT_MAX and LAT_MIN <= max_y <= LAT_MAX):
        raise RodentReportQueryError(f"bbox latitude must be within [{LAT_MIN}, {LAT_MAX}]")
    if min_x > max_x or min_y > max_y:
        raise RodentReportQueryError("bbox must be ordered minX,minY,maxX,maxY")
    if (max_x - min_x) > BBOX_MAX_SPAN or (max_y - min_y) > BBOX_MAX_SPAN:
        raise RodentReportQueryError(
            f"bbox width and height must not exceed {BBOX_MAX_SPAN} degrees"
        )
    return (min_x, min_y, max_x, max_y)


def parse_time(value: str | None, field: str) -> datetime | None:
    if value is None:
        return None
    if not value.strip():
        raise RodentReportQueryError(f"{field} must not be empty")
    try:
        return parse_rfc3339_utc(value)
    except ValueError as exc:
        raise RodentReportQueryError(f"{field} must be an RFC3339 UTC timestamp") from exc


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_point(payload: Any) -> RodentReportPoint:
    if isinstance(payload, (str, bytes)):
        try:
            payload = json.loads(payload)
        except ValueError as exc:
            raise RodentReportDataError(INVALID_GEOMETRY_MESSAGE) from exc
    if not isinstance(payload, Mapping) or payload.get("type") != "Point":
        raise RodentReportDataError(INVALID_GEOMETRY_MESSAGE)
    coordinates = payload.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) != 2:
        raise RodentReportDataError(INVALID_GEOMETRY_MESSAGE)
    x, y = coordinates
    if (
        not isinstance(x, (int, float))
        or isinstance(x, bool)
        or not isinstance(y, (int, float))
        or isinstance(y, bool)
        or not math.isfinite(x)
        or not math.isfinite(y)
        or not (LON_MIN <= x <= LON_MAX)
        or not (LAT_MIN <= y <= LAT_MAX)
    ):
        raise RodentReportDataError(INVALID_GEOMETRY_MESSAGE)
    return RodentReportPoint(type="Point", coordinates=[float(x), float(y)])


def _empty_response(
    bbox: tuple[float, float, float, float] | None,
    reported_from: str | None,
    reported_to: str | None,
) -> RodentReportResponse:
    return RodentReportResponse(
        features=[],
        data_state="empty",
        provenance=None,
        feature_count=0,
        bbox=bbox,
        reported_from=reported_from,
        reported_to=reported_to,
        truncated=False,
    )


def list_rodent_reports(
    session: Session,
    *,
    bbox: str | None = None,
    reported_from: str | None = None,
    reported_to: str | None = None,
    dataset_id: str | None = None,
) -> RodentReportResponse:
    """Return the latest fixture version, optionally bbox/time filtered."""
    parsed_bbox = parse_bbox(bbox)
    from_time = parse_time(reported_from, "reported_from")
    to_time = parse_time(reported_to, "reported_to")
    if from_time is not None and to_time is not None and from_time > to_time:
        raise RodentReportQueryError("reported_from must be less than or equal to reported_to")
    echo_from = _format_utc(from_time) if from_time is not None else None
    echo_to = _format_utc(to_time) if to_time is not None else None

    resolved_dataset_id = dataset_id or get_settings().rodent_report_dataset_id
    try:
        meta = (
            session.execute(
                select(
                    RodentReport.resource_version,
                    RodentReport.provenance,
                )
                .where(RodentReport.dataset_id == resolved_dataset_id)
                .order_by(RodentReport.resource_version.desc())
                .limit(1)
            )
            .mappings()
            .first()
        )
    except SQLAlchemyError as exc:
        raise RodentReportStorageError("rodent report storage unavailable") from exc
    if meta is None:
        return _empty_response(parsed_bbox, echo_from, echo_to)

    try:
        provenance = RodentReportProvenanceV1.model_validate(meta["provenance"])
    except ValidationError as exc:
        raise RodentReportDataError("stored rodent report provenance failed validation") from exc

    statement = (
        select(
            RodentReport.source_record_id,
            RodentReport.dataset_id,
            RodentReport.resource_version,
            RodentReport.provenance,
            RodentReport.data_class,
            RodentReport.classification,
            RodentReport.report_type,
            RodentReport.reported_at,
            RodentReport.location_precision,
            RodentReport.review_status,
            RodentReport.municipal_status,
            RodentReport.action_status,
            func.ST_AsGeoJSON(RodentReport.geometry).label("geometry"),
        )
        .where(RodentReport.dataset_id == resolved_dataset_id)
        .where(RodentReport.resource_version == meta["resource_version"])
        .order_by(RodentReport.reported_at, RodentReport.source_record_id)
        .limit(FEATURE_CAP + 1)
    )
    if parsed_bbox is not None:
        min_x, min_y, max_x, max_y = parsed_bbox
        statement = statement.where(
            func.ST_Intersects(
                RodentReport.geometry,
                func.ST_MakeEnvelope(min_x, min_y, max_x, max_y, 4326),
            )
        )
    if from_time is not None:
        statement = statement.where(RodentReport.reported_at >= from_time)
    if to_time is not None:
        statement = statement.where(RodentReport.reported_at <= to_time)
    try:
        rows = session.execute(statement).mappings().all()
    except SQLAlchemyError as exc:
        raise RodentReportStorageError("rodent report storage unavailable") from exc

    truncated = len(rows) > FEATURE_CAP
    rows = rows[:FEATURE_CAP]

    features: list[RodentReportFeature] = []
    for row in rows:
        if (
            row["dataset_id"] != resolved_dataset_id
            or row["resource_version"] != meta["resource_version"]
            or row["provenance"] != meta["provenance"]
        ):
            raise RodentReportDataError("persisted rodent report rows span multiple source groups")
        if row["data_class"] != RODENT_REPORT_DATA_CLASS:
            raise RodentReportDataError("persisted rodent report data_class is inconsistent")
        if row["classification"] != RODENT_REPORT_CLASSIFICATION:
            raise RodentReportDataError("persisted rodent report classification is inconsistent")
        features.append(
            RodentReportFeature(
                id=row["source_record_id"],
                geometry=_parse_point(row["geometry"]),
                properties=RodentReportProperties(
                    report_id=row["source_record_id"],
                    source=SOURCE_KIND,
                    report_type=row["report_type"],
                    reported_at=_format_utc(row["reported_at"]),
                    location_precision=row["location_precision"],
                    review_status=row["review_status"],
                    municipal_status=row["municipal_status"],
                    action_status=row["action_status"],
                    data_class=row["data_class"],
                    classification=row["classification"],
                    provenance_schema_version=provenance.schema_version,
                    dataset_id=row["dataset_id"],
                    resource_version=row["resource_version"],
                    content_sha256=provenance.content_sha256,
                ),
            )
        )

    return RodentReportResponse(
        features=features,
        data_state="available",
        provenance=provenance,
        feature_count=len(features),
        bbox=parsed_bbox,
        reported_from=echo_from,
        reported_to=echo_to,
        truncated=truncated,
    )
