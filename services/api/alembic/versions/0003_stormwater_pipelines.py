"""Add stormwater infrastructure reference pipelines with typed provenance.

Revision ID: 0003_stormwater_pipelines
Revises: 0002_administrative_districts
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0003_stormwater_pipelines"
down_revision: str | None = "0002_administrative_districts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ATTRIBUTE_COLUMNS = (
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


def upgrade() -> None:
    columns = [
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("dataset_id", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.String(length=64), nullable=False),
        sa.Column("resource_version", sa.String(length=64), nullable=False),
        sa.Column("archive_sha256", sa.String(length=64), nullable=False),
        sa.Column("data_class", sa.String(length=32), nullable=False),
        sa.Column("classification", sa.String(length=16), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
    ]
    columns.extend(
        sa.Column(name, sa.String(length=255), nullable=True) for name in _ATTRIBUTE_COLUMNS
    )
    columns.extend(
        [
            sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
        ]
    )
    op.create_table(
        "stormwater_pipelines",
        *columns,
        sa.CheckConstraint(
            "classification IN ('OBSERVED', 'INFERRED', 'SIMULATED', 'UNVERIFIED')",
            name="ck_stormwater_pipelines_classification",
        ),
        sa.CheckConstraint(
            "data_class = 'INFRASTRUCTURE_REFERENCE'",
            name="ck_stormwater_pipelines_data_class",
        ),
        sa.CheckConstraint(
            "GeometryType(geometry) = 'LINESTRING' AND NOT ST_IsEmpty(geometry)",
            name="ck_stormwater_pipelines_geometry",
        ),
        sa.UniqueConstraint(
            "dataset_id",
            "resource_version",
            "source_record_id",
            name="uq_stormwater_pipelines_key",
        ),
    )
    op.create_index(
        "idx_stormwater_pipelines_geometry",
        "stormwater_pipelines",
        ["geometry"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index("idx_stormwater_pipelines_geometry", table_name="stormwater_pipelines")
    op.drop_table("stormwater_pipelines")
