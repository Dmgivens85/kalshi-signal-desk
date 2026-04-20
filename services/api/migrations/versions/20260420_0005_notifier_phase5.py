"""phase 5 notifier tables and delivery metadata"""

from alembic import op
import sqlalchemy as sa


revision = "20260420_0005"
down_revision = "20260420_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("notification_endpoints") as batch_op:
        batch_op.add_column(sa.Column("overnight_critical_only", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("allow_daytime_info", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.add_column(sa.Column("allow_emergency_priority", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("default_deep_link_base", sa.String(length=1024), nullable=True))

    with op.batch_alter_table("notification_deliveries") as batch_op:
        batch_op.add_column(sa.Column("priority", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("urgency", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("overnight_flag", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("quiet_hours_suppressed", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("dedupe_suppressed", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("signal_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_notification_deliveries_signal_id",
            "signals",
            ["signal_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_notification_deliveries_dedupe_key", ["dedupe_key"])
        batch_op.create_index("ix_notification_deliveries_signal_id", ["signal_id"])

    op.create_table(
        "notification_audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "delivery_id",
            sa.String(length=36),
            sa.ForeignKey("notification_deliveries.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "signal_id",
            sa.String(length=36),
            sa.ForeignKey("signals.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="recorded"),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notification_audit_logs_delivery_id", "notification_audit_logs", ["delivery_id"])
    op.create_index("ix_notification_audit_logs_signal_id", "notification_audit_logs", ["signal_id"])
    op.create_index("ix_notification_audit_logs_event_type", "notification_audit_logs", ["event_type"])

    op.create_table(
        "notification_receipts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "delivery_id",
            sa.String(length=36),
            sa.ForeignKey("notification_deliveries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="pushover"),
        sa.Column("receipt", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notification_receipts_delivery_id", "notification_receipts", ["delivery_id"])
    op.create_index("ix_notification_receipts_receipt", "notification_receipts", ["receipt"], unique=True)

    op.create_table(
        "quiet_hour_policies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("timezone_name", sa.String(length=64), nullable=False, server_default="America/New_York"),
        sa.Column("quiet_start_hour", sa.Integer(), nullable=False, server_default="22"),
        sa.Column("quiet_end_hour", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("allow_critical_overnight", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allow_daytime_info", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quiet_hour_policies_user_id", "quiet_hour_policies", ["user_id"])

    op.create_table(
        "user_device_targets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="pushover"),
        sa.Column("device_name", sa.String(length=255), nullable=False),
        sa.Column("destination", sa.String(length=512), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_device_targets_user_id", "user_device_targets", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_device_targets_user_id", table_name="user_device_targets")
    op.drop_table("user_device_targets")

    op.drop_index("ix_quiet_hour_policies_user_id", table_name="quiet_hour_policies")
    op.drop_table("quiet_hour_policies")

    op.drop_index("ix_notification_receipts_receipt", table_name="notification_receipts")
    op.drop_index("ix_notification_receipts_delivery_id", table_name="notification_receipts")
    op.drop_table("notification_receipts")

    op.drop_index("ix_notification_audit_logs_event_type", table_name="notification_audit_logs")
    op.drop_index("ix_notification_audit_logs_signal_id", table_name="notification_audit_logs")
    op.drop_index("ix_notification_audit_logs_delivery_id", table_name="notification_audit_logs")
    op.drop_table("notification_audit_logs")

    with op.batch_alter_table("notification_deliveries") as batch_op:
        batch_op.drop_index("ix_notification_deliveries_signal_id")
        batch_op.drop_index("ix_notification_deliveries_dedupe_key")
        batch_op.drop_constraint("fk_notification_deliveries_signal_id", type_="foreignkey")
        batch_op.drop_column("signal_id")
        batch_op.drop_column("dedupe_suppressed")
        batch_op.drop_column("quiet_hours_suppressed")
        batch_op.drop_column("expires_at")
        batch_op.drop_column("overnight_flag")
        batch_op.drop_column("urgency")
        batch_op.drop_column("priority")

    with op.batch_alter_table("notification_endpoints") as batch_op:
        batch_op.drop_column("default_deep_link_base")
        batch_op.drop_column("allow_emergency_priority")
        batch_op.drop_column("allow_daytime_info")
        batch_op.drop_column("overnight_critical_only")
