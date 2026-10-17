from __future__ import annotations

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Identity,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SpatialArtifact(Base):
    __tablename__ = "spatial_artifacts"
    __table_args__ = (
        CheckConstraint(
            "classification IN ('OBSERVED', 'INFERRED', 'SIMULATED', 'UNVERIFIED')",
            name="ck_spatial_artifacts_classification",
        ),
        Index("idx_spatial_artifacts_geometry", "geometry", postgresql_using="gist"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    artifact_key: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    classification: Mapped[str] = mapped_column(String(16), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    geometry: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False), nullable=True
    )


class AdministrativeDistrict(Base):
    """Provenance-preserving administrative reference district geometry.

    Kept separate from ``spatial_artifacts`` because these are a single,
    dataset-specific layer with its own identity and idempotency key.
    """

    __tablename__ = "administrative_districts"
    __table_args__ = (
        CheckConstraint(
            "classification IN ('OBSERVED', 'INFERRED', 'SIMULATED', 'UNVERIFIED')",
            name="ck_administrative_districts_classification",
        ),
        CheckConstraint(
            "data_class = 'ADMINISTRATIVE_REFERENCE'",
            name="ck_administrative_districts_data_class",
        ),
        CheckConstraint(
            "GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON') AND NOT ST_IsEmpty(geometry)",
            name="ck_administrative_districts_geometry",
        ),
        UniqueConstraint(
            "dataset_id",
            "resource_version",
            "district_id",
            name="uq_administrative_districts_key",
        ),
        Index("idx_administrative_districts_geometry", "geometry", postgresql_using="gist"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    district_id: Mapped[str] = mapped_column(String(64), nullable=False)
    district_name: Mapped[str] = mapped_column(String(160), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_version: Mapped[str] = mapped_column(String(64), nullable=False)
    archive_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    data_class: Mapped[str] = mapped_column(String(32), nullable=False)
    classification: Mapped[str] = mapped_column(String(16), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StormwaterPipeline(Base):
    """Provenance-preserving stormwater infrastructure reference line.

    Endpoint IDs and source attributes are publisher records only; no topology
    or connectivity is represented.
    """

    __tablename__ = "stormwater_pipelines"
    __table_args__ = (
        CheckConstraint(
            "classification IN ('OBSERVED', 'INFERRED', 'SIMULATED', 'UNVERIFIED')",
            name="ck_stormwater_pipelines_classification",
        ),
        CheckConstraint(
            "data_class = 'INFRASTRUCTURE_REFERENCE'",
            name="ck_stormwater_pipelines_data_class",
        ),
        CheckConstraint(
            "GeometryType(geometry) = 'LINESTRING' AND NOT ST_IsEmpty(geometry)",
            name="ck_stormwater_pipelines_geometry",
        ),
        UniqueConstraint(
            "dataset_id",
            "resource_version",
            "source_record_id",
            name="uq_stormwater_pipelines_key",
        ),
        Index("idx_stormwater_pipelines_geometry", "geometry", postgresql_using="gist"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_version: Mapped[str] = mapped_column(String(64), nullable=False)
    archive_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    data_class: Mapped[str] = mapped_column(String(32), nullable=False)
    classification: Mapped[str] = mapped_column(String(16), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    category_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pipe_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_node_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    end_node_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    managing_unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    work_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    installation_date: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dimension_unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    diameter_width: Mapped[str | None] = mapped_column(String(255), nullable=True)
    diameter_height: Mapped[str | None] = mapped_column(String(255), nullable=True)
    conduit_count: Mapped[str | None] = mapped_column(String(255), nullable=True)
    material: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_burial_depth: Mapped[str | None] = mapped_column(String(255), nullable=True)
    end_burial_depth: Mapped[str | None] = mapped_column(String(255), nullable=True)
    length: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pipe_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    use_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RodentReport(Base):
    """Synthetic report-shaped rodent-report fixture point.

    These records are SIMULATED report events, not observations, prevalence,
    population, movement, disease risk, or intervention evidence.
    """

    __tablename__ = "rodent_reports"
    __table_args__ = (
        CheckConstraint(
            "classification = 'SIMULATED'",
            name="ck_rodent_reports_classification",
        ),
        CheckConstraint(
            "data_class = 'RODENT_REPORT'",
            name="ck_rodent_reports_data_class",
        ),
        CheckConstraint(
            "GeometryType(geometry) = 'POINT' AND NOT ST_IsEmpty(geometry)",
            name="ck_rodent_reports_geometry",
        ),
        UniqueConstraint(
            "dataset_id",
            "resource_version",
            "source_record_id",
            name="uq_rodent_reports_key",
        ),
        Index("idx_rodent_reports_geometry", "geometry", postgresql_using="gist"),
        Index(
            "idx_rodent_reports_version_time",
            "dataset_id",
            "resource_version",
            "reported_at",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    source_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_version: Mapped[str] = mapped_column(String(64), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    data_class: Mapped[str] = mapped_column(String(32), nullable=False)
    classification: Mapped[str] = mapped_column(String(16), nullable=False)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location_precision: Mapped[str] = mapped_column(String(32), nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), nullable=False)
    municipal_status: Mapped[str] = mapped_column(String(32), nullable=False)
    action_status: Mapped[str] = mapped_column(String(32), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    geometry: Mapped[Any] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
