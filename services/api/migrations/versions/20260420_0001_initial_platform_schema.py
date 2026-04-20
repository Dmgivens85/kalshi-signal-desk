"""initial platform schema"""

from alembic import op
import sqlalchemy as sa


revision = "20260420_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False, server_default="analyst"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "kalshi_credentials",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_id", sa.String(length=255), nullable=False),
        sa.Column("environment", sa.String(length=32), nullable=False),
        sa.Column("private_key_path", sa.String(length=1024), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "market_snapshots",
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
    op.create_table(
        "signals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("market_ticker", sa.String(length=128), nullable=False),
        sa.Column("signal_type", sa.String(length=64), nullable=False),
        sa.Column("thesis", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("horizon", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("market_title", sa.String(length=512), nullable=True),
        sa.Column("recommended_action", sa.String(length=64), nullable=True),
        sa.Column("reason_summary", sa.Text(), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("feature_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_by_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "enrichments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_record_id", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("market_ref", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("implied_probability", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("normalized_payload", sa.JSON(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "enrichment_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("enrichment_id", sa.String(length=36), sa.ForeignKey("enrichments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("market_ticker", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("strategy", sa.String(length=64), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("manual_override", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "mapping_overrides",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_record_id", sa.String(length=255), nullable=True),
        sa.Column("market_ref", sa.String(length=255), nullable=True),
        sa.Column("target_market_ticker", sa.String(length=128), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("confidence_boost", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("market_ticker", sa.String(length=128), nullable=False),
        sa.Column("client_order_id", sa.String(length=255), nullable=False, unique=True),
        sa.Column("kalshi_order_id", sa.String(length=255), nullable=True),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("order_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("yes_price", sa.Integer(), nullable=True),
        sa.Column("no_price", sa.Integer(), nullable=True),
        sa.Column("approval_status", sa.String(length=32), nullable=False, server_default="not_required"),
        sa.Column("requires_manual_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("approved_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preview_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("risk_check_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_request", sa.JSON(), nullable=False),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "risk_limits",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("max_order_count", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("max_order_notional_cents", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("max_daily_notional_cents", sa.Integer(), nullable=False, server_default="100000"),
        sa.Column("allowed_markets", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "notification_endpoints",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("destination", sa.String(length=512), nullable=False),
        sa.Column("title_prefix", sa.String(length=128), nullable=True),
        sa.Column("device_target", sa.String(length=255), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="pushover"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("filters_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("supports_pwa_push", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("endpoint_id", sa.String(length=36), sa.ForeignKey("notification_endpoints.id"), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="pushover"),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("deep_link_url", sa.String(length=1024), nullable=True),
        sa.Column("provider_receipt", sa.String(length=255), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "execution_audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("order_id", sa.String(length=36), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="recorded"),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "system_controls",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("updated_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_controls")
    op.drop_table("execution_audit_logs")
    op.drop_table("notification_deliveries")
    op.drop_table("notification_endpoints")
    op.drop_table("risk_limits")
    op.drop_table("orders")
    op.drop_table("mapping_overrides")
    op.drop_table("enrichment_mappings")
    op.drop_table("enrichments")
    op.drop_table("signals")
    op.drop_table("market_snapshots")
    op.drop_table("kalshi_credentials")
    op.drop_table("users")
