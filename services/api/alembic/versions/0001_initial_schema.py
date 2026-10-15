"""Create provenance-aware spatial artifact storage and enable PostGIS."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "spatial_artifacts",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("artifact_key", sa.String(length=160), nullable=False, unique=True),
        sa.Column("classification", sa.String(length=16), nullable=False),
        sa.Column(
            "provenance",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "geometry",
            Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.CheckConstraint(
            "classification IN ('OBSERVED', 'INFERRED', 'SIMULATED', 'UNVERIFIED')",
            name="ck_spatial_artifacts_classification",
        ),
    )
    op.create_index(
        "idx_spatial_artifacts_geometry",
        "spatial_artifacts",
        ["geometry"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index("idx_spatial_artifacts_geometry", table_name="spatial_artifacts")
    op.drop_table("spatial_artifacts")
