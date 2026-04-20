import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_kalshi_platform.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./data/test_kalshi_platform.db"

from app.db.models import ExternalMarketMappingRecord, KalshiMarket
from external_enrichment.mappers import MappingEngine
from external_enrichment.normalizers import american_odds_to_probability, consensus_probability, divergence_score
from kalshi_signal_shared import ExternalEntityModel, ExternalEntityType


def test_sportsbook_probability_and_consensus_helpers() -> None:
    probs = [american_odds_to_probability(-150), american_odds_to_probability(+140)]
    assert probs[0] > probs[1]
    assert 0.0 < consensus_probability(probs) < 1.0
    assert divergence_score(probs) >= 0.0


def test_mapping_engine_prefers_explicit_market_ref() -> None:
    engine = MappingEngine()
    entity = ExternalEntityModel(
        source_slug="sportsbook-primary",
        external_id="fed-cut",
        entity_type=ExternalEntityType.MARKET,
        title="Fed cut by June 2026",
        metadata={"market_ref": "FED-2026-CUTS"},
    )
    markets = [
        KalshiMarket(
            ticker="FED-2026-CUTS",
            event_ticker="FED-2026",
            title="Will the Fed deliver a rate cut by June 2026?",
        )
    ]
    mapping = engine.map_entity(entity, markets, [])
    assert mapping is not None
    assert mapping.kalshi_market_ticker == "FED-2026-CUTS"
    assert mapping.strategy == "explicit_market_ref"


def test_mapping_engine_uses_manual_override() -> None:
    engine = MappingEngine()
    entity = ExternalEntityModel(
        source_slug="metaculus",
        external_id="macro-2026",
        entity_type=ExternalEntityType.QUESTION,
        title="Will the US enter recession in 2026?",
    )
    markets = [
        KalshiMarket(
            ticker="US-RECESSION-2026",
            event_ticker="MACRO-2026",
            title="Will the US enter recession in 2026?",
        )
    ]
    overrides = [
        ExternalMarketMappingRecord(
            external_entity_row_id="row-1",
            external_entity_id="macro-2026",
            kalshi_market_ticker="US-RECESSION-2026",
            confidence_score=1.0,
            strategy="manual_override",
            source_notes="Reviewed manually.",
            manual_override=True,
            is_active=True,
        )
    ]
    mapping = engine.map_entity(entity, markets, overrides)
    assert mapping is not None
    assert mapping.manual_override is True
