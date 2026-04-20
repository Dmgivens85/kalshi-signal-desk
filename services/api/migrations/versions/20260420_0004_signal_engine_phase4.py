"""phase 4 signal engine tables and columns"""

from alembic import op
import sqlalchemy as sa


revision = "20260420_0004"
down_revision = "20260420_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_strategies_slug", "strategies", ["slug"])

    op.create_table(
        "signal_features",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("signal_id", sa.String(length=36), sa.ForeignKey("signals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_group", sa.String(length=64), nullable=False),
        sa.Column("feature_name", sa.String(length=128), nullable=False),
        sa.Column("feature_value", sa.Float(), nullable=False),
        sa.Column("feature_unit", sa.String(length=32), nullable=True),
        sa.Column("is_supporting", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("detail_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_signal_features_signal_id", "signal_features", ["signal_id"])
    op.create_index("ix_signal_features_feature_group", "signal_features", ["feature_group"])
    op.create_index("ix_signal_features_feature_name", "signal_features", ["feature_name"])

    op.create_table(
        "alert_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("signal_id", sa.String(length=36), sa.ForeignKey("signals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("market_ticker", sa.String(length=128), nullable=False),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("urgency", sa.String(length=32), nullable=False),
        sa.Column("overnight_flag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_status", sa.String(length=32), nullable=False, server_default="candidate"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alert_events_signal_id", "alert_events", ["signal_id"])
    op.create_index("ix_alert_events_market_ticker", "alert_events", ["market_ticker"])
    op.create_index("ix_alert_events_dedupe_key", "alert_events", ["dedupe_key"])
    op.create_index("ix_alert_events_alert_type", "alert_events", ["alert_type"])
    op.create_index("ix_alert_events_urgency", "alert_events", ["urgency"])

    with op.batch_alter_table("signals") as batch_op:
        batch_op.add_column(sa.Column("strategy_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("direction", sa.String(length=16), nullable=True))
        batch_op.add_column(sa.Column("confidence_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("kalshi_support_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("external_support_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("risk_penalty_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("overnight_priority_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("urgency_tier", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("suggested_position_size_bucket", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("evidence_refs", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("overnight_flag", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("dedupe_key", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("alert_classification", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("notification_candidate_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
        batch_op.create_index("ix_signals_dedupe_key", ["dedupe_key"])
        batch_op.create_foreign_key("fk_signals_strategy_id", "strategies", ["strategy_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("signals") as batch_op:
        batch_op.drop_constraint("fk_signals_strategy_id", type_="foreignkey")
        batch_op.drop_index("ix_signals_dedupe_key")
        batch_op.drop_column("notification_candidate_payload")
        batch_op.drop_column("alert_classification")
        batch_op.drop_column("dedupe_key")
        batch_op.drop_column("overnight_flag")
        batch_op.drop_column("expires_at")
        batch_op.drop_column("evidence_refs")
        batch_op.drop_column("suggested_position_size_bucket")
        batch_op.drop_column("urgency_tier")
        batch_op.drop_column("overnight_priority_score")
        batch_op.drop_column("risk_penalty_score")
        batch_op.drop_column("external_support_score")
        batch_op.drop_column("kalshi_support_score")
        batch_op.drop_column("confidence_score")
        batch_op.drop_column("direction")
        batch_op.drop_column("strategy_id")

    op.drop_index("ix_alert_events_urgency", table_name="alert_events")
    op.drop_index("ix_alert_events_alert_type", table_name="alert_events")
    op.drop_index("ix_alert_events_dedupe_key", table_name="alert_events")
    op.drop_index("ix_alert_events_market_ticker", table_name="alert_events")
    op.drop_index("ix_alert_events_signal_id", table_name="alert_events")
    op.drop_table("alert_events")

    op.drop_index("ix_signal_features_feature_name", table_name="signal_features")
    op.drop_index("ix_signal_features_feature_group", table_name="signal_features")
    op.drop_index("ix_signal_features_signal_id", table_name="signal_features")
    op.drop_table("signal_features")

    op.drop_index("ix_strategies_slug", table_name="strategies")
    op.drop_table("strategies")
