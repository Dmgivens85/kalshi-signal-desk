from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import AlertEventRecord, ExternalMarketMappingRecord, SignalFeatureRecord, SignalRecord
from signal_engine.config import SignalEngineSettings
from signal_engine.consumers import SignalRepository
from signal_engine.explainability import build_explainability
from signal_engine.features import build_kalshi_features, build_unified_signal_input
from signal_engine.models import (
    ComponentScores,
    EnrichmentFeatureSet,
    NotificationCandidate,
    SignalOutput,
    UnifiedSignalInput,
)
from signal_engine.policies import apply_signal_policy
from signal_engine.ranking import rank_actionable
from signal_engine.scorers import score_signal_components


class SignalEngineService:
    STRATEGY_SLUG = "phase4_core_signal_v1"

    def __init__(self, settings: SignalEngineSettings, db: AsyncSession) -> None:
        self.settings = settings
        self.db = db
        self.repository = SignalRepository(db)

    async def run(self) -> dict[str, object]:
        await self.repository.seed_demo_data()
        strategy = await self.repository.get_or_create_strategy(
            self.STRATEGY_SLUG,
            name="Phase 4 Core Signal Strategy",
            description="Kalshi microstructure plus external enrichment fusion with overnight alert policy.",
            config_json={
                "daytime_confidence_threshold": self.settings.daytime_confidence_threshold,
                "overnight_confidence_threshold": self.settings.overnight_confidence_threshold,
            },
        )

        markets = await self.repository.load_markets()
        created: list[SignalRecord] = []
        for market in markets:
            snapshots = await self.repository.load_market_snapshots(market.ticker)
            orderbook_events = await self.repository.load_orderbook_events(market.ticker)
            mappings = await self.repository.load_external_mappings(market.ticker)

            kalshi_features = build_kalshi_features(market, snapshots, orderbook_events)
            enrichment_features, evidence_refs = self._build_enrichment_inputs(mappings)
            unified_input = build_unified_signal_input(
                market,
                kalshi_features,
                enrichment_features,
                evidence_refs=evidence_refs,
            )
            scores = score_signal_components(unified_input)
            recent_alerts = await self.repository.load_recent_alerts(
                dedupe_key=f"{market.ticker}:signal",
                since=datetime.now(timezone.utc) - timedelta(minutes=self.settings.duplicate_suppression_minutes),
            )
            policy = apply_signal_policy(
                unified_input,
                scores,
                self.settings,
                duplicate_found=bool(recent_alerts),
                cooldown_active=False,
            )
            explainability = build_explainability(
                unified_input,
                scores,
                urgency_tier=policy.urgency_tier,
                suggested_action=policy.suggested_action,
                size_bucket=policy.size_bucket,
            )
            direction = "watch"
            if policy.suggested_action == "consider_yes":
                direction = "yes"
            elif policy.suggested_action == "consider_no":
                direction = "no"

            signal = SignalRecord(
                id=str(uuid4()),
                market_ticker=market.ticker,
                market_title=market.title,
                signal_type=self.STRATEGY_SLUG,
                thesis=explainability.summary,
                confidence=scores.confidence_score,
                horizon="intraday to 2 weeks",
                status="active",
                recommended_action=policy.suggested_action,
                reason_summary=explainability.summary,
                source_count=enrichment_features.source_count,
                metadata_json={"scores": scores.model_dump(mode="json")},
                feature_payload={
                    "kalshi_features": kalshi_features.model_dump(mode="json"),
                    "enrichment_features": enrichment_features.model_dump(mode="json"),
                },
                strategy_id=strategy.id,
                direction=direction,
                confidence_score=scores.confidence_score,
                kalshi_support_score=scores.kalshi_support_score,
                external_support_score=scores.external_support_score,
                risk_penalty_score=scores.risk_penalty_score,
                overnight_priority_score=scores.overnight_priority_score,
                urgency_tier=policy.urgency_tier,
                suggested_position_size_bucket=policy.size_bucket,
                evidence_refs=unified_input.evidence_refs,
                expires_at=policy.expires_at,
                overnight_flag=policy.overnight_flag,
                dedupe_key=f"{market.ticker}:signal",
                alert_classification=policy.classification,
                notification_candidate_payload=policy.notification_candidate.model_dump(mode="json")
                if policy.notification_candidate
                else {},
            )
            features = self._build_feature_rows(signal.id, kalshi_features.model_dump(), enrichment_features.model_dump(), scores.model_dump())
            alert_event = None
            if policy.notification_candidate is not None:
                alert_event = AlertEventRecord(
                    market_ticker=market.ticker,
                    dedupe_key=policy.notification_candidate.dedupe_key,
                    alert_type=policy.classification,
                    urgency=policy.notification_candidate.urgency,
                    overnight_flag=policy.notification_candidate.overnight_flag,
                    expires_at=policy.notification_candidate.expiration_time,
                    payload=policy.notification_candidate.model_dump(mode="json"),
                )

            persisted = await self.repository.replace_signal(signal, features, alert_event)
            created.append(persisted)

        await self.db.commit()
        ranked = rank_actionable(created)
        outputs = [self._to_output(signal) for signal in ranked]
        return {"signals_created": len(outputs), "items": [item.model_dump(mode="json") for item in outputs]}

    def _build_enrichment_inputs(
        self,
        mappings: list[ExternalMarketMappingRecord],
    ) -> tuple[EnrichmentFeatureSet, list[dict[str, object]]]:
        if not mappings:
            return EnrichmentFeatureSet(), []
        latest_feature = mappings[0].feature_snapshot or {}
        feature = EnrichmentFeatureSet(
            external_support_score=float(latest_feature.get("external_support_score", 0.0)),
            consensus_delta=float(latest_feature.get("consensus_delta", 0.0)),
            disagreement_score=float(latest_feature.get("disagreement_score", 0.0)),
            source_count=int(latest_feature.get("source_count", len(mappings))),
            recency_score=float(latest_feature.get("recency_score", 0.0)),
            catalyst_presence=bool(latest_feature.get("catalyst_presence", False)),
            catalysts=list(latest_feature.get("catalysts", [])),
        )
        evidence_refs = [
            {
                "mapping_id": mapping.id,
                "source_notes": mapping.source_notes,
                "strategy": mapping.strategy,
                "confidence_score": mapping.confidence_score,
            }
            for mapping in mappings[:5]
        ]
        return feature, evidence_refs

    def _build_feature_rows(
        self,
        signal_id: str,
        kalshi_features: dict[str, float | int | bool | list | dict],
        enrichment_features: dict[str, float | int | bool | list | dict],
        scores: dict[str, float | int | bool | list | dict],
    ) -> list[SignalFeatureRecord]:
        rows: list[SignalFeatureRecord] = []
        for group_name, values in {
            "kalshi": kalshi_features,
            "enrichment": enrichment_features,
            "scores": scores,
        }.items():
            for name, value in values.items():
                if isinstance(value, bool):
                    numeric = 1.0 if value else 0.0
                elif isinstance(value, (int, float)):
                    numeric = float(value)
                else:
                    continue
                rows.append(
                    SignalFeatureRecord(
                        signal_id=signal_id,
                        feature_group=group_name,
                        feature_name=name,
                        feature_value=numeric,
                        is_supporting=numeric >= 0,
                        detail_json={},
                    )
                )
        return rows

    def _to_output(self, signal: SignalRecord) -> SignalOutput:
        payload = signal.notification_candidate_payload or None
        return SignalOutput(
            signal_id=signal.id,
            market_ticker=signal.market_ticker,
            direction=signal.direction or "watch",
            confidence_score=signal.confidence_score or signal.confidence,
            kalshi_support_score=signal.kalshi_support_score or 0.0,
            external_support_score=signal.external_support_score or 0.0,
            risk_penalty_score=signal.risk_penalty_score or 0.0,
            urgency_tier=signal.urgency_tier or "digest",
            suggested_action=signal.recommended_action or "watch",
            suggested_position_size_bucket=signal.suggested_position_size_bucket or "small",
            reason_summary=signal.reason_summary or signal.thesis,
            evidence_refs=signal.evidence_refs,
            created_at=signal.created_at,
            expires_at=signal.expires_at,
            overnight_flag=signal.overnight_flag,
            overnight_priority_score=signal.overnight_priority_score or 0.0,
            alert_classification=signal.alert_classification or "digest_only",
            explainability=build_explainability(
                UnifiedSignalInput.model_validate(
                    {
                        "market_ticker": signal.market_ticker,
                        "market_title": signal.market_title or signal.market_ticker,
                        "market_price": 0.5,
                        "kalshi_features": signal.feature_payload.get("kalshi_features", {}),
                        "enrichment_features": signal.feature_payload.get("enrichment_features", {}),
                        "evidence_refs": signal.evidence_refs,
                    }
                ),
                ComponentScores.model_validate(signal.metadata_json.get("scores", {})),
                urgency_tier=signal.urgency_tier or "digest",
                suggested_action=signal.recommended_action or "watch",
                size_bucket=signal.suggested_position_size_bucket or "small",
            ),
            notification_candidate=payload and NotificationCandidate.model_validate(payload),
        )


async def run_loop(settings: SignalEngineSettings) -> None:
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        while True:
            async with session_factory() as session:
                service = SignalEngineService(settings, session)
                await service.run()
            await asyncio.sleep(settings.loop_interval_seconds)
    finally:
        await engine.dispose()
