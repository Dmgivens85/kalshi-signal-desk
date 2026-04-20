"""phase 7 selective automation tables and metadata"""

from alembic import op
import sqlalchemy as sa


revision = "20260420_0007"
down_revision = "20260420_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

    op.create_table(
        "automation_policies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("strategy_id", sa.String(length=36), sa.ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("strategy_slug", sa.String(length=64), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("user_opt_in_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allowed_market_tickers", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("allowed_categories", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("min_confidence_score", sa.Float(), nullable=False, server_default="0.9"),
        sa.Column("overnight_min_confidence_score", sa.Float(), nullable=False, server_default="0.96"),
        sa.Column("max_size_bucket", sa.String(length=32), nullable=False, server_default="small"),
        sa.Column("max_open_automated_positions", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_automation_policies_name", "automation_policies", ["name"], unique=True)
    op.create_index("ix_automation_policies_strategy_id", "automation_policies", ["strategy_id"])
    op.create_index("ix_automation_policies_strategy_slug", "automation_policies", ["strategy_slug"])

    op.create_table(
        "automation_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("signal_id", sa.String(length=36), sa.ForeignKey("signals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("strategy_id", sa.String(length=36), sa.ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("order_id", sa.String(length=36), sa.ForeignKey("orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("policy_id", sa.String(length=36), sa.ForeignKey("automation_policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mode", sa.String(length=32), nullable=False, server_default="dry_run"),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("decision_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("result_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("kalshi_order_id", sa.String(length=255), nullable=True),
        sa.Column("anomaly_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_automation_runs_signal_id", "automation_runs", ["signal_id"])
    op.create_index("ix_automation_runs_strategy_id", "automation_runs", ["strategy_id"])
    op.create_index("ix_automation_runs_order_id", "automation_runs", ["order_id"])
    op.create_index("ix_automation_runs_policy_id", "automation_runs", ["policy_id"])
    op.create_index("ix_automation_runs_status", "automation_runs", ["status"])

    op.create_table(
        "automation_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("automation_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("signal_id", sa.String(length=36), sa.ForeignKey("signals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False, server_default="info"),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_automation_events_run_id", "automation_events", ["run_id"])
    op.create_index("ix_automation_events_signal_id", "automation_events", ["signal_id"])
    op.create_index("ix_automation_events_event_type", "automation_events", ["event_type"])
    op.create_index("ix_automation_events_status", "automation_events", ["status"])

    op.create_table(
        "automation_pauses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("policy_id", sa.String(length=36), sa.ForeignKey("automation_policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("triggered_by", sa.String(length=32), nullable=False, server_default="system"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("resume_reason", sa.Text(), nullable=True),
        sa.Column("resumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resumed_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_automation_pauses_policy_id", "automation_pauses", ["policy_id"])

    op.create_table(
        "automation_failures",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("automation_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("policy_id", sa.String(length=36), sa.ForeignKey("automation_policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("failure_type", sa.String(length=64), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_automation_failures_run_id", "automation_failures", ["run_id"])
    op.create_index("ix_automation_failures_policy_id", "automation_failures", ["policy_id"])
    op.create_index("ix_automation_failures_failure_type", "automation_failures", ["failure_type"])


def downgrade() -> None:
    op.drop_index("ix_automation_failures_failure_type", table_name="automation_failures")
    op.drop_index("ix_automation_failures_policy_id", table_name="automation_failures")
    op.drop_index("ix_automation_failures_run_id", table_name="automation_failures")
    op.drop_table("automation_failures")

    op.drop_index("ix_automation_pauses_policy_id", table_name="automation_pauses")
    op.drop_table("automation_pauses")

    op.drop_index("ix_automation_events_status", table_name="automation_events")
    op.drop_index("ix_automation_events_event_type", table_name="automation_events")
    op.drop_index("ix_automation_events_signal_id", table_name="automation_events")
    op.drop_index("ix_automation_events_run_id", table_name="automation_events")
    op.drop_table("automation_events")

    op.drop_index("ix_automation_runs_status", table_name="automation_runs")
    op.drop_index("ix_automation_runs_policy_id", table_name="automation_runs")
    op.drop_index("ix_automation_runs_order_id", table_name="automation_runs")
    op.drop_index("ix_automation_runs_strategy_id", table_name="automation_runs")
    op.drop_index("ix_automation_runs_signal_id", table_name="automation_runs")
    op.drop_table("automation_runs")

    op.drop_index("ix_automation_policies_strategy_slug", table_name="automation_policies")
    op.drop_index("ix_automation_policies_strategy_id", table_name="automation_policies")
    op.drop_index("ix_automation_policies_name", table_name="automation_policies")
    op.drop_table("automation_policies")

    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_column("metadata_json")
