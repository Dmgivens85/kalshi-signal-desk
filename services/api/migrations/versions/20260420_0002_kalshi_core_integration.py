"""phase 2 kalshi core integration tables"""

from alembic import op
import sqlalchemy as sa


revision = "20260420_0002"
down_revision = "20260420_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kalshi_markets",
        sa.Column("ticker", sa.String(length=128), primary_key=True),
        sa.Column("event_ticker", sa.String(length=128), nullable=False),
        sa.Column("series_ticker", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("subtitle", sa.String(length=512), nullable=True),
        sa.Column("market_type", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_price", sa.Integer(), nullable=True),
        sa.Column("yes_bid", sa.Integer(), nullable=True),
        sa.Column("yes_ask", sa.Integer(), nullable=True),
        sa.Column("volume", sa.Integer(), nullable=True),
        sa.Column("open_interest", sa.Integer(), nullable=True),
        sa.Column("liquidity", sa.Integer(), nullable=True),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_kalshi_markets_event_ticker", "kalshi_markets", ["event_ticker"])
    op.create_index("ix_kalshi_markets_series_ticker", "kalshi_markets", ["series_ticker"])

    op.execute(
        """
        INSERT INTO kalshi_markets (
            ticker, event_ticker, title, status, close_time, last_price, yes_bid, yes_ask, volume, open_interest,
            raw_payload, created_at, updated_at, last_observed_at
        )
        SELECT
            market_ticker, event_ticker, title, status, close_time, last_price, yes_bid, yes_ask, volume, open_interest,
            raw_payload, created_at, updated_at, updated_at
        FROM market_snapshots
        """
    )

    op.create_table(
        "market_snapshots_v2",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("market_ticker", sa.String(length=128), sa.ForeignKey("kalshi_markets.ticker", ondelete="CASCADE"), nullable=False),
        sa.Column("event_ticker", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_price", sa.Integer(), nullable=True),
        sa.Column("yes_bid", sa.Integer(), nullable=True),
        sa.Column("yes_ask", sa.Integer(), nullable=True),
        sa.Column("volume", sa.Integer(), nullable=True),
        sa.Column("open_interest", sa.Integer(), nullable=True),
        sa.Column("snapshot_type", sa.String(length=32), nullable=False, server_default="legacy"),
        sa.Column("sequence_number", sa.Integer(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bid_levels", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("ask_levels", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        """
        INSERT INTO market_snapshots_v2 (
            id, market_ticker, event_ticker, title, status, close_time, last_price, yes_bid, yes_ask, volume,
            open_interest, snapshot_type, sequence_number, observed_at, bid_levels, ask_levels, raw_payload,
            created_at, updated_at
        )
        SELECT
            id, market_ticker, event_ticker, title, status, close_time, last_price, yes_bid, yes_ask, volume,
            open_interest, 'legacy', NULL, updated_at, '[]', '[]', raw_payload, created_at, updated_at
        FROM market_snapshots
        """
    )
    op.drop_table("market_snapshots")
    op.rename_table("market_snapshots_v2", "market_snapshots")
    op.create_index("ix_market_snapshots_market_ticker", "market_snapshots", ["market_ticker"])
    op.create_index("ix_market_snapshots_event_ticker", "market_snapshots", ["event_ticker"])
    op.create_index("ix_market_snapshots_observed_at", "market_snapshots", ["observed_at"])

    op.create_table(
        "orderbook_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("market_ticker", sa.String(length=128), sa.ForeignKey("kalshi_markets.ticker", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=True),
        sa.Column("side", sa.String(length=8), nullable=True),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("delta", sa.Integer(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bid_levels", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("ask_levels", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_orderbook_events_market_ticker", "orderbook_events", ["market_ticker"])
    op.create_index("ix_orderbook_events_event_type", "orderbook_events", ["event_type"])
    op.create_index("ix_orderbook_events_observed_at", "orderbook_events", ["observed_at"])

    op.create_table(
        "service_health_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("service_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_index("ix_service_health_events_service_name", "service_health_events", ["service_name"])
    op.create_index("ix_service_health_events_status", "service_health_events", ["status"])
    op.create_index("ix_service_health_events_observed_at", "service_health_events", ["observed_at"])


def downgrade() -> None:
    op.drop_index("ix_service_health_events_observed_at", table_name="service_health_events")
    op.drop_index("ix_service_health_events_status", table_name="service_health_events")
    op.drop_index("ix_service_health_events_service_name", table_name="service_health_events")
    op.drop_table("service_health_events")

    op.drop_index("ix_orderbook_events_observed_at", table_name="orderbook_events")
    op.drop_index("ix_orderbook_events_event_type", table_name="orderbook_events")
    op.drop_index("ix_orderbook_events_market_ticker", table_name="orderbook_events")
    op.drop_table("orderbook_events")

    op.create_table(
        "market_snapshots_legacy",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("market_ticker", sa.String(length=128), nullable=False, unique=True),
        sa.Column("event_ticker", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_price", sa.Integer(), nullable=True),
        sa.Column("yes_bid", sa.Integer(), nullable=True),
        sa.Column("yes_ask", sa.Integer(), nullable=True),
        sa.Column("volume", sa.Integer(), nullable=True),
        sa.Column("open_interest", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute(
        """
        INSERT INTO market_snapshots_legacy (
            id, market_ticker, event_ticker, title, status, close_time, last_price, yes_bid, yes_ask, volume,
            open_interest, raw_payload, created_at, updated_at
        )
        SELECT
            id, market_ticker, event_ticker, title, status, close_time, last_price, yes_bid, yes_ask, volume,
            open_interest, raw_payload, created_at, updated_at
        FROM market_snapshots
        """
    )
    op.drop_index("ix_market_snapshots_observed_at", table_name="market_snapshots")
    op.drop_index("ix_market_snapshots_event_ticker", table_name="market_snapshots")
    op.drop_index("ix_market_snapshots_market_ticker", table_name="market_snapshots")
    op.drop_table("market_snapshots")
    op.rename_table("market_snapshots_legacy", "market_snapshots")

    op.drop_index("ix_kalshi_markets_series_ticker", table_name="kalshi_markets")
    op.drop_index("ix_kalshi_markets_event_ticker", table_name="kalshi_markets")
    op.drop_table("kalshi_markets")
