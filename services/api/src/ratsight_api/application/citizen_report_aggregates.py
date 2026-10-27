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
from dataclasses import dataclass
from typing import Any, cast

from pydantic import ValidationError
from ratsight_api.api.schemas import (
    CitizenReportAggregateProvenance,
    CitizenReportAggregateResponse,
    CitizenReportCellFeature,
    CitizenReportCellPolygon,
    CitizenReportCellProperties,
    CitizenReportClassification,
    CitizenReportDataClass,
    CitizenReportOriginEligibility,
    CitizenReportOriginEligibilityReason,
    CitizenReportProvenanceV1,
    CitizenReportSourceKind,
    OriginSourceIdentity,
    SyntheticAggregateFixtureProvenance,
)
from ratsight_api.domain.citizen_report_aggregates import (
    ATTRIBUTION,
    BBOX_MAX_SPAN,
    CELL_SIZE_METERS,
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
    ORIGIN_ELIGIBILITY_MESSAGES,
    ORIGIN_POLICY_VERSION,
    SOURCE_KIND,
    SOURCE_URL,
    SYNTHETIC_FIXTURE_ATTRIBUTION,
    SYNTHETIC_FIXTURE_CLASSIFICATION,
    SYNTHETIC_FIXTURE_DATA_CLASS,
    SYNTHETIC_FIXTURE_DATASET_PREFIX,
    SYNTHETIC_FIXTURE_NOTICE,
    SYNTHETIC_FIXTURE_SOURCE_KIND,
    origin_eligibility,
    synthetic_aggregate_fixture_enabled,
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


def _parse_polygon(
    payload: Any,
    *,
    data_class: CitizenReportDataClass = CITIZEN_REPORT_DATA_CLASS,
    classification: CitizenReportClassification = CITIZEN_REPORT_CLASSIFICATION,
    source_kind: CitizenReportSourceKind = SOURCE_KIND,
) -> CitizenReportCellPolygon:
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
    return CitizenReportCellPolygon(
        coordinates=coordinates,
        data_class=data_class,
        classification=classification,
        source_kind=source_kind,
    )


def _ensure_dataset_allowed(dataset_id: str) -> bool:
    is_fixture = dataset_id.startswith(SYNTHETIC_FIXTURE_DATASET_PREFIX)
    if is_fixture and not synthetic_aggregate_fixture_enabled(dataset_id):
        raise CitizenReportQueryError(
            "synthetic aggregate fixtures require an explicit ratsight-smoke dataset and opt-in"
        )
    return is_fixture


def _validated_provenance(dataset_id: str, payload: Any) -> CitizenReportAggregateProvenance:
    is_fixture = _ensure_dataset_allowed(dataset_id)
    try:
        provenance = (
            SyntheticAggregateFixtureProvenance.model_validate(payload)
            if is_fixture
            else CitizenReportProvenanceV1.model_validate(payload)
        )
    except ValidationError as exc:
        raise CitizenReportDataError("stored citizen report provenance failed validation") from exc
    if provenance.dataset_id != dataset_id:
        raise CitizenReportDataError("stored aggregate provenance dataset identity does not match")
    return provenance


class CitizenReportCellNotFound(LookupError):
    """Raised when a requested aggregate cell identity is not stored."""


class CitizenReportDatasetUnknown(LookupError):
    """Raised when the requested dataset identity has no published snapshot."""


class CitizenReportSourceVersionConflict(RuntimeError):
    """Raised when the requested snapshot is not the currently published one."""


class CitizenReportOriginIneligible(ValueError):
    """Raised when a published cell's report category cannot seed a simulation."""

    def __init__(self, reason: str) -> None:
        super().__init__(ORIGIN_ELIGIBILITY_MESSAGES.get(reason, reason))
        self.reason = reason


@dataclass(frozen=True)
class CitizenReportOriginCell:
    """One published cell resolved inside its exact source snapshot.

    Geometry, classification, and suppression state all come from the same
    stored row, so a caller never mixes versions.
    """

    feature_id: str
    polygon: CitizenReportCellPolygon
    dataset_id: str
    resource_version: str
    content_sha256: str
    cell_id: str
    month: str
    report_type: str
    report_type_eligible: bool
    report_type_reason: str
    policy_version: str
    cell_size_meters: int
    source_url: str | None
    attribution: str | None


def parse_origin_feature_id(feature_id: str) -> tuple[str, str, str]:
    """Split 'cell_id:month:report_type' from the right; cell ids may contain colons."""
    parts = feature_id.rsplit(":", 2)
    if len(parts) != 3:
        raise CitizenReportQueryError("origin cell id must be cell_id:month:report_type")
    cell_id, month, report_type = parts
    if not cell_id or MONTH_RE.fullmatch(month) is None or not report_type:
        raise CitizenReportQueryError("origin cell id must be cell_id:month:report_type")
    return cell_id, month, report_type


def _latest_published_snapshot(session: Session, dataset_id: str) -> tuple[str, str] | None:
    """Return the published (resource_version, content_sha256) for a dataset.

    Version and digest are read together, so a client cannot be told its version
    is current while its digest is compared against a different snapshot.
    """
    try:
        row = (
            session.execute(
                select(CitizenReportCell.resource_version, CitizenReportCell.content_sha256)
                .where(CitizenReportCell.dataset_id == dataset_id)
                .order_by(CitizenReportCell.resource_version.desc())
                .limit(1)
            )
            .mappings()
            .first()
        )
    except SQLAlchemyError as exc:
        raise CitizenReportStorageError("citizen report storage unavailable") from exc
    if row is None:
        return None
    return str(row["resource_version"]), str(row["content_sha256"])


def get_citizen_report_origin_cell(
    session: Session, feature_id: str, source: OriginSourceIdentity
) -> CitizenReportOriginCell:
    """Resolve one origin cell against the exact snapshot the client selected.

    The requested dataset/version/hash must still be the published snapshot; a
    newer import produces a version conflict rather than silently resolving
    against different geometry. The row query pins the same version and digest,
    so published-cell, suppression, and classification rules are applied to that
    snapshot only. There is no fallback, nearest-cell search, or geometry
    synthesis.
    """
    cell_id, month, report_type = parse_origin_feature_id(feature_id)
    _ensure_dataset_allowed(source.dataset_id)
    published = _latest_published_snapshot(session, source.dataset_id)
    if published is None:
        raise CitizenReportDatasetUnknown(
            f"no citizen report aggregate snapshot is published for {source.dataset_id!r}"
        )
    published_version, published_digest = published
    if published_version != source.resource_version or published_digest != source.content_sha256:
        raise CitizenReportSourceVersionConflict(
            "the requested citizen report snapshot is no longer the published version"
        )
    try:
        row = (
            session.execute(
                select(
                    CitizenReportCell.data_class,
                    CitizenReportCell.classification,
                    CitizenReportCell.report_count,
                    CitizenReportCell.content_sha256,
                    CitizenReportCell.provenance,
                    func.ST_AsGeoJSON(CitizenReportCell.geometry).label("geometry"),
                )
                .where(CitizenReportCell.dataset_id == source.dataset_id)
                .where(CitizenReportCell.resource_version == source.resource_version)
                .where(CitizenReportCell.content_sha256 == source.content_sha256)
                .where(CitizenReportCell.cell_id == cell_id)
                .where(CitizenReportCell.month == month)
                .where(CitizenReportCell.report_type == report_type)
                .limit(1)
            )
            .mappings()
            .first()
        )
    except SQLAlchemyError as exc:
        raise CitizenReportStorageError("citizen report storage unavailable") from exc
    if row is None:
        raise CitizenReportCellNotFound(
            "origin cell is not present in the selected citizen report aggregate snapshot"
        )
    provenance = _validated_provenance(source.dataset_id, row["provenance"])
    if (
        provenance.resource_version != source.resource_version
        or provenance.content_sha256 != source.content_sha256
    ):
        raise CitizenReportDataError(
            "stored origin provenance does not match the requested snapshot"
        )
    expected_data_class = (
        SYNTHETIC_FIXTURE_DATA_CLASS
        if isinstance(provenance, SyntheticAggregateFixtureProvenance)
        else CITIZEN_REPORT_DATA_CLASS
    )
    expected_classification = (
        SYNTHETIC_FIXTURE_CLASSIFICATION
        if isinstance(provenance, SyntheticAggregateFixtureProvenance)
        else CITIZEN_REPORT_CLASSIFICATION
    )
    if row["data_class"] != expected_data_class or row["classification"] != expected_classification:
        raise CitizenReportDataError("stored origin cell classification is invalid")
    if isinstance(provenance, SyntheticAggregateFixtureProvenance):
        if row["report_count"] is not None:
            raise CitizenReportDataError("synthetic fixture origin must not contain report counts")
    elif row["report_count"] is None or row["report_count"] < 3:
        # A suppressed row must be indistinguishable from an absent one: reporting
        # "suppressed" would confirm that the cell exists in the source snapshot.
        raise CitizenReportCellNotFound(
            "origin cell is not present in the selected citizen report aggregate snapshot"
        )
    # Category eligibility is checked only after the cell is proven published and
    # suppression-eligible, so an error cannot reveal a suppressed cell.
    eligible, reason = origin_eligibility(report_type)
    if not eligible:
        raise CitizenReportOriginIneligible(reason)
    polygon = _parse_polygon(
        row["geometry"],
        data_class=expected_data_class,
        classification=expected_classification,
        source_kind=provenance.source_kind,
    )
    return CitizenReportOriginCell(
        feature_id=feature_id,
        polygon=polygon,
        dataset_id=source.dataset_id,
        resource_version=source.resource_version,
        content_sha256=source.content_sha256,
        cell_id=cell_id,
        month=month,
        report_type=report_type,
        report_type_eligible=eligible,
        report_type_reason=reason,
        policy_version=ORIGIN_POLICY_VERSION,
        cell_size_meters=CELL_SIZE_METERS,
        source_url=(
            SYNTHETIC_FIXTURE_ATTRIBUTION
            if isinstance(provenance, SyntheticAggregateFixtureProvenance)
            else SOURCE_URL
        ),
        attribution=(
            SYNTHETIC_FIXTURE_ATTRIBUTION
            if isinstance(provenance, SyntheticAggregateFixtureProvenance)
            else ATTRIBUTION
        ),
    )


def origin_eligibility_payload(report_type: str) -> CitizenReportOriginEligibility:
    """Build the API eligibility payload from the single domain rule."""
    eligible, reason = origin_eligibility(report_type)
    return CitizenReportOriginEligibility(
        eligible=eligible,
        reason=cast(CitizenReportOriginEligibilityReason, reason),
        policy_version=ORIGIN_POLICY_VERSION,
        message=ORIGIN_ELIGIBILITY_MESSAGES[reason],
    )


def _empty_response(
    bbox: tuple[float, float, float, float] | None,
    *,
    is_fixture: bool = False,
) -> CitizenReportAggregateResponse:
    return CitizenReportAggregateResponse(
        features=[],
        data_state="empty",
        data_class=(SYNTHETIC_FIXTURE_DATA_CLASS if is_fixture else CITIZEN_REPORT_DATA_CLASS),
        classification=(
            SYNTHETIC_FIXTURE_CLASSIFICATION if is_fixture else CITIZEN_REPORT_CLASSIFICATION
        ),
        notice=SYNTHETIC_FIXTURE_NOTICE if is_fixture else NOTICE,
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
    is_fixture = _ensure_dataset_allowed(resolved_dataset_id)
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
        return _empty_response(parsed_bbox, is_fixture=is_fixture)

    provenance = _validated_provenance(resolved_dataset_id, meta["provenance"])
    if provenance.resource_version != meta["resource_version"]:
        raise CitizenReportDataError("stored aggregate provenance version does not match")

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
    expected_data_class = SYNTHETIC_FIXTURE_DATA_CLASS if is_fixture else CITIZEN_REPORT_DATA_CLASS
    expected_classification = (
        SYNTHETIC_FIXTURE_CLASSIFICATION if is_fixture else CITIZEN_REPORT_CLASSIFICATION
    )
    expected_source_kind = SYNTHETIC_FIXTURE_SOURCE_KIND if is_fixture else SOURCE_KIND
    for row in rows[:FEATURE_CAP]:
        if row["data_class"] != expected_data_class:
            raise CitizenReportDataError("stored aggregate data_class is invalid")
        if row["classification"] != expected_classification:
            raise CitizenReportDataError("stored aggregate classification is invalid")
        if is_fixture and row["report_count"] is not None:
            raise CitizenReportDataError("synthetic fixtures must not contain report counts")
        if not is_fixture and (row["report_count"] is None or row["report_count"] < 3):
            raise CitizenReportDataError(
                "stored citizen report aggregate is below suppression minimum"
            )
        features.append(
            CitizenReportCellFeature(
                id=f"{row['cell_id']}:{row['month']}:{row['report_type']}",
                geometry=_parse_polygon(
                    row["geometry"],
                    data_class=expected_data_class,
                    classification=expected_classification,
                    source_kind=expected_source_kind,
                ),
                properties=CitizenReportCellProperties(
                    cell_id=row["cell_id"],
                    month=row["month"],
                    report_type=row["report_type"],
                    count=row["report_count"],
                    data_class=expected_data_class,
                    classification=expected_classification,
                    attribution=(SYNTHETIC_FIXTURE_ATTRIBUTION if is_fixture else ATTRIBUTION),
                    origin_eligibility=origin_eligibility_payload(row["report_type"]),
                ),
            )
        )

    return CitizenReportAggregateResponse(
        features=features,
        data_state="available" if features else "empty",
        data_class=expected_data_class,
        classification=expected_classification,
        notice=SYNTHETIC_FIXTURE_NOTICE if is_fixture else NOTICE,
        provenance=provenance,
        feature_count=len(features),
        bbox=parsed_bbox,
        truncated=truncated,
    )
