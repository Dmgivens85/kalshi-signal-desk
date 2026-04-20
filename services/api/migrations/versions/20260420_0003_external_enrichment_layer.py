"""phase 3 external enrichment layer"""

from alembic import op
import sqlalchemy as sa


revision = "20260420_0003"
down_revision = "20260420_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_sources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="configured"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_external_sources_slug", "external_sources", ["slug"])
    op.create_index("ix_external_sources_category", "external_sources", ["category"])

    op.create_table(
        "external_entities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_id", sa.String(length=36), sa.ForeignKey("external_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("resolution_criteria", sa.Text(), nullable=True),
        sa.Column("current_probability", sa.Float(), nullable=True),
        sa.Column("forecast_value", sa.Float(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_external_entities_source_id", "external_entities", ["source_id"])
    op.create_index("ix_external_entities_external_id", "external_entities", ["external_id"])
    op.create_index("ix_external_entities_entity_type", "external_entities", ["entity_type"])

    op.create_table(
        "external_market_mappings",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("external_entity_row_id", sa.String(length=36), sa.ForeignKey("external_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_entity_id", sa.String(length=255), nullable=False),
        sa.Column("kalshi_market_ticker", sa.String(length=128), sa.ForeignKey("kalshi_markets.ticker", ondelete="CASCADE"), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("strategy", sa.String(length=64), nullable=False),
        sa.Column("source_notes", sa.Text(), nullable=False),
        sa.Column("manual_override", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("mismatch_reasons", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("ambiguity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("feature_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_external_market_mappings_external_entity_row_id", "external_market_mappings", ["external_entity_row_id"])
    op.create_index("ix_external_market_mappings_external_entity_id", "external_market_mappings", ["external_entity_id"])
    op.create_index("ix_external_market_mappings_kalshi_market_ticker", "external_market_mappings", ["kalshi_market_ticker"])

    op.create_table(
        "external_observations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_id", sa.String(length=36), sa.ForeignKey("external_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_entity_row_id", sa.String(length=36), sa.ForeignKey("external_entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_entity_id", sa.String(length=255), nullable=False),
        sa.Column("observation_type", sa.String(length=32), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("probability_value", sa.Float(), nullable=True),
        sa.Column("numeric_value", sa.Float(), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("entities", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("raw_text_available", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ai_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_external_observations_source_id", "external_observations", ["source_id"])
    op.create_index("ix_external_observations_external_entity_row_id", "external_observations", ["external_entity_row_id"])
    op.create_index("ix_external_observations_external_entity_id", "external_observations", ["external_entity_id"])
    op.create_index("ix_external_observations_observation_type", "external_observations", ["observation_type"])
    op.create_index("ix_external_observations_observed_at", "external_observations", ["observed_at"])


def downgrade() -> None:
    op.drop_index("ix_external_observations_observed_at", table_name="external_observations")
    op.drop_index("ix_external_observations_observation_type", table_name="external_observations")
    op.drop_index("ix_external_observations_external_entity_id", table_name="external_observations")
    op.drop_index("ix_external_observations_external_entity_row_id", table_name="external_observations")
    op.drop_index("ix_external_observations_source_id", table_name="external_observations")
    op.drop_table("external_observations")

    op.drop_index("ix_external_market_mappings_kalshi_market_ticker", table_name="external_market_mappings")
    op.drop_index("ix_external_market_mappings_external_entity_id", table_name="external_market_mappings")
    op.drop_index("ix_external_market_mappings_external_entity_row_id", table_name="external_market_mappings")
    op.drop_table("external_market_mappings")

    op.drop_index("ix_external_entities_entity_type", table_name="external_entities")
    op.drop_index("ix_external_entities_external_id", table_name="external_entities")
    op.drop_index("ix_external_entities_source_id", table_name="external_entities")
    op.drop_table("external_entities")

    op.drop_index("ix_external_sources_category", table_name="external_sources")
    op.drop_index("ix_external_sources_slug", table_name="external_sources")
    op.drop_table("external_sources")
