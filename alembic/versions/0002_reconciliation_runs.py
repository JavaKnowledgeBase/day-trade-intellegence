"""Add reconciliation_runs table for broker synchronization history."""

from alembic import op
import sqlalchemy as sa

revision = "0002_reconciliation_runs"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reconciliation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("checked_symbols", sa.Integer(), nullable=False),
        sa.Column("mismatched_symbols", sa.Integer(), nullable=False),
        sa.Column("detail", sa.String(length=512), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reconciliation_runs_status", "reconciliation_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_reconciliation_runs_status", table_name="reconciliation_runs")
    op.drop_table("reconciliation_runs")
