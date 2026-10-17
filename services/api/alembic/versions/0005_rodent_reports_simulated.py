"""Require SIMULATED classification for fixture-only rodent reports.

Revision ID: 0005_rodent_reports_simulated
Revises: 0004_rodent_reports
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_rodent_reports_simulated"
down_revision: str | None = "0004_rodent_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CLASSIFICATION_CONSTRAINT = "ck_rodent_reports_classification"
TABLE = "rodent_reports"


def upgrade() -> None:
    op.drop_constraint(CLASSIFICATION_CONSTRAINT, TABLE, type_="check")
    op.create_check_constraint(
        CLASSIFICATION_CONSTRAINT,
        TABLE,
        "classification = 'SIMULATED'",
    )


def downgrade() -> None:
    op.drop_constraint(CLASSIFICATION_CONSTRAINT, TABLE, type_="check")
    op.create_check_constraint(
        CLASSIFICATION_CONSTRAINT,
        TABLE,
        "classification IN ('OBSERVED', 'INFERRED', 'SIMULATED', 'UNVERIFIED')",
    )
