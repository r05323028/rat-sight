"""Remove the synthetic rodent-report layer.

Revision ID: 0008_remove_rodent_reports
Revises: 0007_citizen_report_cells

The synthetic fixture was removed from the API, importer, and UI. This
forward migration removes its rows and schema, including the immutability
guard created by earlier revisions. Citizen-report aggregates are the only
remaining report layer.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008_remove_rodent_reports"
down_revision: str | None = "0007_citizen_report_cells"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS rodent_reports_immutable ON rodent_reports")
    op.execute("DROP FUNCTION IF EXISTS prevent_rodent_report_mutation()")
    op.execute("DROP TABLE IF EXISTS rodent_reports")


def downgrade() -> None:
    # Destructive removal; restoring synthetic rows is not an automatic downgrade.
    pass
