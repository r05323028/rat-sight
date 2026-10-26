"""Create the suppressed citizen-report aggregate table.

Revision ID: 0007_citizen_report_cells
Revises: 0006_rodent_reports_immutability
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0007_citizen_report_cells"
down_revision: str | None = "0006_rodent_reports_immutability"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "citizen_report_cells"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("dataset_id", sa.String(64), nullable=False),
        sa.Column("resource_version", sa.String(64), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("data_class", sa.String(32), nullable=False),
        sa.Column("classification", sa.String(16), nullable=False),
        sa.Column("cell_id", sa.String(64), nullable=False),
        sa.Column("month", sa.String(7), nullable=False),
        sa.Column("report_type", sa.String(32), nullable=False),
        sa.Column("report_count", sa.Integer(), nullable=False),
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
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "classification = 'UNVERIFIED'",
            name="ck_citizen_report_cells_classification",
        ),
        sa.CheckConstraint(
            "data_class = 'CITIZEN_REPORT_AGGREGATE'",
            name="ck_citizen_report_cells_data_class",
        ),
        sa.CheckConstraint("report_count >= 3", name="ck_citizen_report_cells_minimum"),
        sa.CheckConstraint(
            "GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON') AND NOT ST_IsEmpty(geometry)",
            name="ck_citizen_report_cells_geometry",
        ),
        sa.UniqueConstraint(
            "dataset_id",
            "resource_version",
            "cell_id",
            "month",
            "report_type",
            name="uq_citizen_report_cells_key",
        ),
    )
    op.create_index(
        "idx_citizen_report_cells_geometry",
        TABLE,
        ["geometry"],
        postgresql_using="gist",
    )
    op.create_index(
        "idx_citizen_report_cells_version_month",
        TABLE,
        ["dataset_id", "resource_version", "month"],
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_citizen_report_cell_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'citizen report aggregates are immutable after import';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER citizen_report_cells_immutable
        BEFORE UPDATE OR DELETE ON citizen_report_cells
        FOR EACH ROW EXECUTE FUNCTION prevent_citizen_report_cell_mutation();
        """
    )


def downgrade() -> None:
    op.execute(f"DROP TRIGGER IF EXISTS citizen_report_cells_immutable ON {TABLE}")
    op.execute("DROP FUNCTION IF EXISTS prevent_citizen_report_cell_mutation()")
    op.drop_index("idx_citizen_report_cells_version_month", table_name=TABLE)
    op.drop_index("idx_citizen_report_cells_geometry", table_name=TABLE)
    op.drop_table(TABLE)
