from __future__ import annotations

from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, CheckConstraint, Identity, String, text
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
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    artifact_key: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    classification: Mapped[str] = mapped_column(String(16), nullable=False)
    provenance: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    geometry: Mapped[Any | None] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True
    )
