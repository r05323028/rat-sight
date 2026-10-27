"""Allow count-free, simulated aggregate fixtures in disposable smoke datasets.

Revision ID: 0009_synthetic_aggregate_smoke_fixture
Revises: 0008_remove_rodent_reports
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_synthetic_agg_fixture"
down_revision: str | None = "0008_remove_rodent_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "citizen_report_cells"


def upgrade() -> None:
    op.drop_constraint("ck_citizen_report_cells_classification", _TABLE, type_="check")
    op.drop_constraint("ck_citizen_report_cells_data_class", _TABLE, type_="check")
    op.drop_constraint("ck_citizen_report_cells_minimum", _TABLE, type_="check")
    op.alter_column(
        _TABLE,
        "report_count",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.create_check_constraint(
        "ck_citizen_report_cells_classification",
        _TABLE,
        "(data_class = 'CITIZEN_REPORT_AGGREGATE' AND classification = 'UNVERIFIED') OR "
        "(data_class = 'SYNTHETIC_AGGREGATE_FIXTURE' AND classification = 'SIMULATED')",
    )
    op.create_check_constraint(
        "ck_citizen_report_cells_data_class",
        _TABLE,
        "data_class IN ('CITIZEN_REPORT_AGGREGATE', 'SYNTHETIC_AGGREGATE_FIXTURE')",
    )
    op.create_check_constraint(
        "ck_citizen_report_cells_minimum",
        _TABLE,
        "(data_class = 'CITIZEN_REPORT_AGGREGATE' AND report_count IS NOT NULL "
        "AND report_count >= 3) OR "
        "(data_class = 'SYNTHETIC_AGGREGATE_FIXTURE' AND report_count IS NULL)",
    )


def downgrade() -> None:
    # Recreating the original constraints below fails and rolls back if fixture rows exist.
    op.drop_constraint("ck_citizen_report_cells_classification", _TABLE, type_="check")
    op.drop_constraint("ck_citizen_report_cells_data_class", _TABLE, type_="check")
    op.drop_constraint("ck_citizen_report_cells_minimum", _TABLE, type_="check")
    op.alter_column(
        _TABLE,
        "report_count",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_citizen_report_cells_classification",
        _TABLE,
        "classification = 'UNVERIFIED'",
    )
    op.create_check_constraint(
        "ck_citizen_report_cells_data_class",
        _TABLE,
        "data_class = 'CITIZEN_REPORT_AGGREGATE'",
    )
    op.create_check_constraint(
        "ck_citizen_report_cells_minimum",
        _TABLE,
        "report_count >= 3",
    )
