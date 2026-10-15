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
