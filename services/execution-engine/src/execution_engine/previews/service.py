from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketSnapshot, SignalRecord
from execution_engine.models import ApprovalStatus, MarketConditions, OrderPreview, SuggestedAction, TradeCandidate
from execution_engine.risk import DeterministicRiskEngine


class PreviewService:
    def __init__(self, db: AsyncSession, risk_engine: DeterministicRiskEngine) -> None:
        self.db = db
        self.risk_engine = risk_engine

    async def build_candidate_from_signal(self, signal_id: str) -> TradeCandidate:
        signal = await self.db.get(SignalRecord, signal_id)
        if signal is None:
            raise ValueError("Signal not found.")
        direction = signal.direction or (
            "yes" if signal.recommended_action == "buy_yes" else "no" if signal.recommended_action == "buy_no" else "watch"
        )
        side = "yes" if direction == "yes" else "no"
        action = "buy" if direction in {"yes", "no"} else "watch"
        price = None
        if signal.feature_payload and isinstance(signal.feature_payload, dict):
            snapshot = signal.feature_payload.get("market_snapshot") or {}
            price = snapshot.get("last_price")
        count = 5 if (signal.confidence_score or signal.confidence or 0.5) < 0.75 else 12
        return TradeCandidate(
            signal_id=signal.id,
            market_ticker=signal.market_ticker,
            side=side,
            action=action,
            count=count,
            yes_price=price if side == "yes" and price is not None else None,
            no_price=(100 - price) if side == "no" and price is not None else None,
            signal_summary=signal.reason_summary or signal.thesis,
            confidence_score=signal.confidence_score or signal.confidence,
            overnight_flag=signal.overnight_flag,
            evidence_refs=signal.evidence_refs or [],
        )

    async def preview(self, candidate: TradeCandidate) -> OrderPreview:
        risk = await self.risk_engine.evaluate(candidate)
        snapshot = (
            await self.db.execute(
                select(MarketSnapshot).where(MarketSnapshot.market_ticker == candidate.market_ticker).order_by(desc(MarketSnapshot.observed_at))
            )
        ).scalar_one_or_none()
        conditions = MarketConditions(
            last_price=snapshot.last_price if snapshot else candidate.yes_price or candidate.no_price,
            best_bid=snapshot.yes_bid if snapshot else None,
            best_ask=snapshot.yes_ask if snapshot else None,
            spread_cents=(snapshot.yes_ask - snapshot.yes_bid) if snapshot and snapshot.yes_ask is not None and snapshot.yes_bid is not None else None,
            liquidity=snapshot.liquidity if snapshot else None,
            volume=snapshot.volume if snapshot else None,
            time_to_resolution_minutes=max(0, int((snapshot.close_time - snapshot.observed_at).total_seconds() / 60)) if snapshot and snapshot.close_time else None,
        )
        status = ApprovalStatus.PENDING_APPROVAL if risk.passed else ApprovalStatus.BLOCKED
        next_action = SuggestedAction.APPROVE if risk.passed else SuggestedAction.BLOCK
        return OrderPreview(
            ticker=candidate.market_ticker,
            side=candidate.side,
            action=candidate.action,
            size_suggestion=risk.size_recommendation,
            suggested_count=candidate.count,
            indicative_price_data=conditions,
            supporting_signal_summary=candidate.signal_summary,
            risk_evaluation_summary=(
                "Deterministic checks passed and the order may proceed to manual approval."
                if risk.passed
                else "Deterministic checks blocked this proposal."
            ),
            recommended_next_action=next_action,
            approval_status=status,
            risk_evaluation=risk,
            candidate_order={
                "ticker": candidate.market_ticker,
                "side": candidate.side,
                "action": candidate.action,
                "count": candidate.count,
                "yes_price": candidate.yes_price,
                "no_price": candidate.no_price,
                "type": candidate.order_type,
                "time_in_force": candidate.time_in_force,
                "post_only": candidate.post_only,
                "reduce_only": candidate.reduce_only,
            },
        )
