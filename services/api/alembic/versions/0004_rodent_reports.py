"""Add fixture-only synthetic rodent report points with typed provenance.

Revision ID: 0004_rodent_reports
Revises: 0003_stormwater_pipelines
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0004_rodent_reports"
down_revision: str | None = "0003_stormwater_pipelines"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rodent_reports",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("source_record_id", sa.String(length=128), nullable=False),
        sa.Column("dataset_id", sa.String(length=64), nullable=False),
        sa.Column("resource_version", sa.String(length=64), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("data_class", sa.String(length=32), nullable=False),
        sa.Column("classification", sa.String(length=16), nullable=False),
        sa.Column("report_type", sa.String(length=32), nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location_precision", sa.String(length=32), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("municipal_status", sa.String(length=32), nullable=False),
        sa.Column("action_status", sa.String(length=32), nullable=False),
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
        sa.CheckConstraint(
            "classification IN ('OBSERVED', 'INFERRED', 'SIMULATED', 'UNVERIFIED')",
            name="ck_rodent_reports_classification",
        ),
        sa.CheckConstraint(
            "data_class = 'RODENT_REPORT'",
            name="ck_rodent_reports_data_class",
        ),
        sa.CheckConstraint(
            "GeometryType(geometry) = 'POINT' AND NOT ST_IsEmpty(geometry)",
            name="ck_rodent_reports_geometry",
        ),
        sa.UniqueConstraint(
            "dataset_id",
            "resource_version",
            "source_record_id",
            name="uq_rodent_reports_key",
        ),
    )
    op.create_index(
        "idx_rodent_reports_geometry",
        "rodent_reports",
        ["geometry"],
        postgresql_using="gist",
    )
    op.create_index(
        "idx_rodent_reports_version_time",
        "rodent_reports",
        ["dataset_id", "resource_version", "reported_at"],
    )
    op.execute(
        """
        CREATE FUNCTION prevent_rodent_report_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'rodent_reports are immutable after import';
        END;
        $$;
        CREATE TRIGGER rodent_reports_immutable
        BEFORE UPDATE OR DELETE ON rodent_reports
        FOR EACH ROW EXECUTE FUNCTION prevent_rodent_report_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS rodent_reports_immutable ON rodent_reports")
    op.execute("DROP FUNCTION IF EXISTS prevent_rodent_report_mutation()")
    op.drop_index("idx_rodent_reports_version_time", table_name="rodent_reports")
    op.drop_index("idx_rodent_reports_geometry", table_name="rodent_reports")
    op.drop_table("rodent_reports")
