"""Ensure the rodent_reports immutability trigger exists on existing databases.

Revision ID: 0006_rodent_reports_immutability
Revises: 0005_rodent_reports_simulated

Some databases applied `0004_rodent_reports` before the `rodent_reports_immutable`
trigger was added to that revision, so `alembic upgrade` does not install it.
This forward repair migration idempotently (re)creates the function and trigger.
It never weakens or removes the guard; a fresh database already receives it from
`0004` and this migration is a no-op-equivalent replacement.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006_rodent_reports_immutability"
down_revision: str | None = "0005_rodent_reports_simulated"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_rodent_report_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'rodent_reports are immutable after import';
        END;
        $$;
        """
    )
    op.execute("DROP TRIGGER IF EXISTS rodent_reports_immutable ON rodent_reports")
    op.execute(
        """
        CREATE TRIGGER rodent_reports_immutable
        BEFORE UPDATE OR DELETE ON rodent_reports
        FOR EACH ROW EXECUTE FUNCTION prevent_rodent_report_mutation();
        """
    )


def downgrade() -> None:
    # The trigger is owned by revision 0004; leave it installed on downgrade.
    pass
