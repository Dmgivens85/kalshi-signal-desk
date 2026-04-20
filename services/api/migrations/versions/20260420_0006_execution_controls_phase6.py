"""phase 6 execution controls, positions, and risk events"""

from alembic import op
import sqlalchemy as sa


revision = "20260420_0006"
down_revision = "20260420_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "positions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("market_ticker", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("side", sa.String(length=16), nullable=True),
        sa.Column("contracts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_entry_price", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exposure_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("realized_pnl_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unrealized_pnl_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_positions_market_ticker", "positions", ["market_ticker"])

    op.create_table(
        "fills",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("order_id", sa.String(length=36), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("position_id", sa.String(length=36), sa.ForeignKey("positions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kalshi_fill_id", sa.String(length=255), nullable=False),
        sa.Column("market_ticker", sa.String(length=128), nullable=False),
        sa.Column("side", sa.String(length=16), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("fee_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fills_order_id", "fills", ["order_id"])
    op.create_index("ix_fills_position_id", "fills", ["position_id"])
    op.create_index("ix_fills_kalshi_fill_id", "fills", ["kalshi_fill_id"], unique=True)
    op.create_index("ix_fills_market_ticker", "fills", ["market_ticker"])

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("order_id", sa.String(length=36), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("decided_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_approval_requests_order_id", "approval_requests", ["order_id"])
    op.create_index("ix_approval_requests_status", "approval_requests", ["status"])

    op.create_table(
        "risk_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("order_id", sa.String(length=36), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("market_ticker", sa.String(length=128), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="info"),
        sa.Column("rule_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="recorded"),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_risk_events_order_id", "risk_events", ["order_id"])
    op.create_index("ix_risk_events_market_ticker", "risk_events", ["market_ticker"])
    op.create_index("ix_risk_events_rule_name", "risk_events", ["rule_name"])

    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("signal_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("position_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("time_in_force", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("post_only", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("reduce_only", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("price", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("rejected_by_user_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("category", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("theme", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("size_bucket", sa.String(length=32), nullable=True))
        batch_op.create_foreign_key("fk_orders_signal_id", "signals", ["signal_id"], ["id"], ondelete="SET NULL")
        batch_op.create_foreign_key("fk_orders_position_id", "positions", ["position_id"], ["id"], ondelete="SET NULL")

    with op.batch_alter_table("risk_limits") as batch_op:
        batch_op.add_column(sa.Column("max_exposure_per_market_cents", sa.Integer(), nullable=False, server_default="25000"))
        batch_op.add_column(sa.Column("max_exposure_per_category_cents", sa.Integer(), nullable=False, server_default="75000"))
        batch_op.add_column(sa.Column("max_simultaneous_positions", sa.Integer(), nullable=False, server_default="8"))
        batch_op.add_column(sa.Column("max_spread_cents", sa.Integer(), nullable=False, server_default="12"))
        batch_op.add_column(sa.Column("min_liquidity", sa.Integer(), nullable=False, server_default="100"))
        batch_op.add_column(sa.Column("max_category_concentration", sa.Float(), nullable=False, server_default="0.55"))
        batch_op.add_column(sa.Column("cooldown_after_loss_minutes", sa.Integer(), nullable=False, server_default="90"))
        batch_op.add_column(sa.Column("min_time_to_resolution_minutes", sa.Integer(), nullable=False, server_default="60"))
        batch_op.add_column(sa.Column("overnight_max_spread_cents", sa.Integer(), nullable=False, server_default="8"))
        batch_op.add_column(sa.Column("overnight_min_liquidity", sa.Integer(), nullable=False, server_default="250"))


def downgrade() -> None:
    with op.batch_alter_table("risk_limits") as batch_op:
        batch_op.drop_column("overnight_min_liquidity")
        batch_op.drop_column("overnight_max_spread_cents")
        batch_op.drop_column("min_time_to_resolution_minutes")
        batch_op.drop_column("cooldown_after_loss_minutes")
        batch_op.drop_column("max_category_concentration")
        batch_op.drop_column("min_liquidity")
        batch_op.drop_column("max_spread_cents")
        batch_op.drop_column("max_simultaneous_positions")
        batch_op.drop_column("max_exposure_per_category_cents")
        batch_op.drop_column("max_exposure_per_market_cents")

    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_constraint("fk_orders_position_id", type_="foreignkey")
        batch_op.drop_constraint("fk_orders_signal_id", type_="foreignkey")
        batch_op.drop_column("size_bucket")
        batch_op.drop_column("theme")
        batch_op.drop_column("category")
        batch_op.drop_column("canceled_at")
        batch_op.drop_column("rejected_at")
        batch_op.drop_column("rejected_by_user_id")
        batch_op.drop_column("price")
        batch_op.drop_column("reduce_only")
        batch_op.drop_column("post_only")
        batch_op.drop_column("time_in_force")
        batch_op.drop_column("position_id")
        batch_op.drop_column("signal_id")

    op.drop_index("ix_risk_events_rule_name", table_name="risk_events")
    op.drop_index("ix_risk_events_market_ticker", table_name="risk_events")
    op.drop_index("ix_risk_events_order_id", table_name="risk_events")
    op.drop_table("risk_events")

    op.drop_index("ix_approval_requests_status", table_name="approval_requests")
    op.drop_index("ix_approval_requests_order_id", table_name="approval_requests")
    op.drop_table("approval_requests")

    op.drop_index("ix_fills_market_ticker", table_name="fills")
    op.drop_index("ix_fills_kalshi_fill_id", table_name="fills")
    op.drop_index("ix_fills_position_id", table_name="fills")
    op.drop_index("ix_fills_order_id", table_name="fills")
    op.drop_table("fills")

    op.drop_index("ix_positions_market_ticker", table_name="positions")
    op.drop_table("positions")
