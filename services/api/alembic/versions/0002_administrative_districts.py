"""Add administrative reference district boundaries with provenance.

Revision ID: 0002_administrative_districts
Revises: 0001_initial_schema
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0002_administrative_districts"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "administrative_districts",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("district_id", sa.String(length=64), nullable=False),
        sa.Column("district_name", sa.String(length=160), nullable=False),
        sa.Column("dataset_id", sa.String(length=64), nullable=False),
        sa.Column("resource_version", sa.String(length=64), nullable=False),
        sa.Column("archive_sha256", sa.String(length=64), nullable=False),
        sa.Column("data_class", sa.String(length=32), nullable=False),
        sa.Column("classification", sa.String(length=16), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "geometry",
            Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "classification IN ('OBSERVED', 'INFERRED', 'SIMULATED', 'UNVERIFIED')",
            name="ck_administrative_districts_classification",
        ),
        sa.CheckConstraint(
            "data_class = 'ADMINISTRATIVE_REFERENCE'",
            name="ck_administrative_districts_data_class",
        ),
        sa.CheckConstraint(
            "GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON') AND NOT ST_IsEmpty(geometry)",
            name="ck_administrative_districts_geometry",
        ),
        sa.UniqueConstraint(
            "dataset_id",
            "resource_version",
            "district_id",
            name="uq_administrative_districts_key",
        ),
    )
    op.create_index(
        "idx_administrative_districts_geometry",
        "administrative_districts",
        ["geometry"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index(
        "idx_administrative_districts_geometry",
        table_name="administrative_districts",
    )
    op.drop_table("administrative_districts")
