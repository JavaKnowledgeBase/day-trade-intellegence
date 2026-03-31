"""Initial schema for audit logs, strategy runs, trade orders, and positions."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trade_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("detail", sa.String(length=512), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trade_audit_logs_symbol", "trade_audit_logs", ["symbol"])
    op.create_index("ix_trade_audit_logs_status", "trade_audit_logs", ["status"])

    op.create_table(
        "strategy_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("timeframe", sa.String(length=32), nullable=False),
        sa.Column("short_window", sa.Integer(), nullable=False),
        sa.Column("long_window", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reason", sa.String(length=512), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_strategy_runs_symbol", "strategy_runs", ["symbol"])

    op.create_table(
        "trade_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_price", sa.Float(), nullable=False),
        sa.Column("broker_order_id", sa.String(length=64), nullable=True),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_trade_orders_symbol", "trade_orders", ["symbol"])
    op.create_index("ix_trade_orders_status", "trade_orders", ["status"])
    op.create_index("ix_trade_orders_broker_order_id", "trade_orders", ["broker_order_id"])

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("average_price", sa.Float(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("symbol", name="uq_positions_symbol"),
    )
    op.create_index("ix_positions_symbol", "positions", ["symbol"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_positions_symbol", table_name="positions")
    op.drop_table("positions")
    op.drop_index("ix_trade_orders_broker_order_id", table_name="trade_orders")
    op.drop_index("ix_trade_orders_status", table_name="trade_orders")
    op.drop_index("ix_trade_orders_symbol", table_name="trade_orders")
    op.drop_table("trade_orders")
    op.drop_index("ix_strategy_runs_symbol", table_name="strategy_runs")
    op.drop_table("strategy_runs")
    op.drop_index("ix_trade_audit_logs_status", table_name="trade_audit_logs")
    op.drop_index("ix_trade_audit_logs_symbol", table_name="trade_audit_logs")
    op.drop_table("trade_audit_logs")
