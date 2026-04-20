"""phase 8 paper trading, portfolio snapshots, and replay runs"""

from alembic import op
import sqlalchemy as sa


revision = "20260420_0008"
down_revision = "20260420_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("market_snapshots") as batch_op:
        batch_op.add_column(sa.Column("liquidity", sa.Integer(), nullable=True))

    op.create_table(
        "paper_orders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_order_id", sa.String(length=36), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("signal_id", sa.String(length=36), sa.ForeignKey("signals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("market_ticker", sa.String(length=128), nullable=False),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("order_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="submitted"),
        sa.Column("requested_count", sa.Integer(), nullable=False),
        sa.Column("filled_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remaining_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reference_price", sa.Integer(), nullable=True),
        sa.Column("simulated_average_fill_price", sa.Integer(), nullable=True),
        sa.Column("fill_mode", sa.String(length=32), nullable=False, server_default="midpoint"),
        sa.Column("is_automation", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_paper_orders_source_order_id", "paper_orders", ["source_order_id"])
    op.create_index("ix_paper_orders_signal_id", "paper_orders", ["signal_id"])
    op.create_index("ix_paper_orders_market_ticker", "paper_orders", ["market_ticker"])

    op.create_table(
        "paper_fills",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("paper_order_id", sa.String(length=36), sa.ForeignKey("paper_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("market_ticker", sa.String(length=128), nullable=False),
        sa.Column("side", sa.String(length=16), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("fee_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("simulated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_paper_fills_paper_order_id", "paper_fills", ["paper_order_id"])
    op.create_index("ix_paper_fills_market_ticker", "paper_fills", ["market_ticker"])

    op.create_table(
        "paper_positions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("signal_id", sa.String(length=36), sa.ForeignKey("signals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("market_ticker", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("side", sa.String(length=16), nullable=True),
        sa.Column("contracts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_entry_price", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exposure_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("realized_pnl_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unrealized_pnl_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("entry_confidence_score", sa.Float(), nullable=True),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_paper_positions_signal_id", "paper_positions", ["signal_id"])
    op.create_index("ix_paper_positions_market_ticker", "paper_positions", ["market_ticker"])

    op.create_table(
        "paper_portfolio_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("cash_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("equity_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("realized_pnl_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unrealized_pnl_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exposure_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False, server_default="replay"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="created"),
        sa.Column("market_ticker", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("summary_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_simulation_runs_name", "simulation_runs", ["name"])
    op.create_index("ix_simulation_runs_market_ticker", "simulation_runs", ["market_ticker"])


def downgrade() -> None:
    with op.batch_alter_table("market_snapshots") as batch_op:
        batch_op.drop_column("liquidity")

    op.drop_index("ix_simulation_runs_market_ticker", table_name="simulation_runs")
    op.drop_index("ix_simulation_runs_name", table_name="simulation_runs")
    op.drop_table("simulation_runs")

    op.drop_table("paper_portfolio_snapshots")

    op.drop_index("ix_paper_positions_market_ticker", table_name="paper_positions")
    op.drop_index("ix_paper_positions_signal_id", table_name="paper_positions")
    op.drop_table("paper_positions")

    op.drop_index("ix_paper_fills_market_ticker", table_name="paper_fills")
    op.drop_index("ix_paper_fills_paper_order_id", table_name="paper_fills")
    op.drop_table("paper_fills")

    op.drop_index("ix_paper_orders_market_ticker", table_name="paper_orders")
    op.drop_index("ix_paper_orders_signal_id", table_name="paper_orders")
    op.drop_index("ix_paper_orders_source_order_id", table_name="paper_orders")
    op.drop_table("paper_orders")
