from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ExecutionAuditRecord,
    FillRecord,
    MarketSnapshot,
    OrderRecord,
    PaperFillRecord,
    PaperOrderRecord,
    PaperPortfolioSnapshotRecord,
    PaperPositionRecord,
    PositionRecord,
    SignalRecord,
    SimulationRunRecord,
)
from execution_engine.models import ApprovalStatus
from execution_engine.paper.models import PaperFillMode, PaperOrderOutcome, PaperPerformanceSnapshot, ReplayRequest, ReplayResult


class PaperExecutionService:
    def __init__(self, db: AsyncSession, *, fill_mode: str = "midpoint", slippage_bps: int = 25, partial_fill_ratio: float = 0.5, default_cash_cents: int = 1_000_000) -> None:
        self.db = db
        self.fill_mode = fill_mode
        self.slippage_bps = slippage_bps
        self.partial_fill_ratio = partial_fill_ratio
        self.default_cash_cents = default_cash_cents

    async def submit_order(self, order: OrderRecord, actor_user_id: str | None) -> dict[str, object]:
        snapshot = (
            await self.db.execute(
                select(MarketSnapshot).where(MarketSnapshot.market_ticker == order.market_ticker).order_by(desc(MarketSnapshot.observed_at))
            )
        ).scalar_one_or_none()
        reference_price = order.price or order.yes_price or order.no_price or (snapshot.last_price if snapshot else 50) or 50
        fill_price = self._fill_price(reference_price)
        fill_count = self._fill_count(order.count, snapshot.liquidity if snapshot else None)
        remaining = max(0, order.count - fill_count)
        status = ApprovalStatus.FILLED.value if remaining == 0 else ApprovalStatus.PARTIALLY_FILLED.value if fill_count > 0 else ApprovalStatus.SUBMITTED.value

        paper_order = PaperOrderRecord(
            source_order_id=order.id,
            signal_id=order.signal_id,
            market_ticker=order.market_ticker,
            side=order.side,
            action=order.action,
            order_type=order.order_type,
            status=status,
            requested_count=order.count,
            filled_count=fill_count,
            remaining_count=remaining,
            reference_price=reference_price,
            simulated_average_fill_price=fill_price if fill_count else None,
            fill_mode=self.fill_mode,
            is_automation=bool(order.metadata_json.get("automation_source")),
            metadata_json={"paper_only": True, "source_order_id": order.id},
        )
        self.db.add(paper_order)
        await self.db.flush()

        order.status = status
        order.raw_response = {"paper": True, "paper_order_id": paper_order.id, "status": status}
        order.kalshi_order_id = None

        if fill_count > 0:
            paper_fill = PaperFillRecord(
                paper_order_id=paper_order.id,
                market_ticker=order.market_ticker,
                side=order.side,
                price=fill_price,
                count=fill_count,
                fee_cents=0,
                simulated_at=datetime.now(timezone.utc),
                metadata_json={"paper_only": True},
            )
            self.db.add(paper_fill)
            await self._upsert_paper_position(order, fill_count, fill_price)

        self.db.add(
            ExecutionAuditRecord(
                order_id=order.id,
                actor_user_id=actor_user_id,
                event_type="paper_order_submitted",
                status=status,
                detail="Order simulated in paper mode without sending to Kalshi.",
                payload={"paper_order_id": paper_order.id, "filled_count": fill_count, "remaining_count": remaining, "fill_price": fill_price},
            )
        )
        await self.capture_portfolio_snapshot()
        await self.db.commit()
        await self.db.refresh(paper_order)
        return {
            "mode": "paper",
            "order": order.to_dict(),
            "paper_order": paper_order.to_dict(),
            "simulated": True,
        }

    async def list_orders(self) -> list[PaperOrderRecord]:
        return list((await self.db.execute(select(PaperOrderRecord).order_by(PaperOrderRecord.created_at.desc()))).scalars().all())

    async def get_order(self, paper_order_id: str) -> PaperOrderRecord | None:
        return (await self.db.execute(select(PaperOrderRecord).where(PaperOrderRecord.id == paper_order_id))).scalar_one_or_none()

    async def list_positions(self) -> list[PaperPositionRecord]:
        return list((await self.db.execute(select(PaperPositionRecord).order_by(PaperPositionRecord.created_at.desc()))).scalars().all())

    async def performance(self) -> PaperPerformanceSnapshot:
        positions = await self.list_positions()
        open_positions = [position for position in positions if position.is_open]
        closed_positions = [position for position in positions if not position.is_open]
        exposure_by_market: dict[str, int] = defaultdict(int)
        exposure_by_category: dict[str, int] = defaultdict(int)
        for position in open_positions:
            exposure_by_market[position.market_ticker] += position.exposure_cents
            exposure_by_category[position.category or "general"] += position.exposure_cents
        wins = [position for position in closed_positions if position.realized_pnl_cents > 0]
        avg_confidence = 0.0
        if positions:
            avg_confidence = sum(position.entry_confidence_score or 0.0 for position in positions) / len(positions)
        return PaperPerformanceSnapshot(
            open_positions=len(open_positions),
            closed_positions=len(closed_positions),
            realized_pnl_cents=sum(position.realized_pnl_cents for position in positions),
            unrealized_pnl_cents=sum(position.unrealized_pnl_cents for position in open_positions),
            exposure_by_market=dict(exposure_by_market),
            exposure_by_category=dict(exposure_by_category),
            win_rate=(len(wins) / len(closed_positions)) if closed_positions else 0.0,
            average_confidence=avg_confidence,
        )

    async def capture_portfolio_snapshot(self) -> PaperPortfolioSnapshotRecord:
        perf = await self.performance()
        snapshot = PaperPortfolioSnapshotRecord(
            cash_cents=self.default_cash_cents - perf.realized_pnl_cents,
            equity_cents=self.default_cash_cents + perf.realized_pnl_cents + perf.unrealized_pnl_cents,
            realized_pnl_cents=perf.realized_pnl_cents,
            unrealized_pnl_cents=perf.unrealized_pnl_cents,
            exposure_json={"market": perf.exposure_by_market, "category": perf.exposure_by_category},
            metadata_json={"paper_only": True},
        )
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def _upsert_paper_position(self, order: OrderRecord, fill_count: int, fill_price: int) -> None:
        position = (
            await self.db.execute(
                select(PaperPositionRecord).where(PaperPositionRecord.market_ticker == order.market_ticker, PaperPositionRecord.is_open.is_(True))
            )
        ).scalar_one_or_none()
        if position is None:
            signal = await self.db.get(SignalRecord, order.signal_id) if order.signal_id else None
            position = PaperPositionRecord(
                signal_id=order.signal_id,
                market_ticker=order.market_ticker,
                category=order.category,
                side=order.side,
                contracts_count=0,
                average_entry_price=0,
                exposure_cents=0,
                entry_confidence_score=signal.confidence_score if signal and signal.confidence_score is not None else (signal.confidence if signal else None),
                metadata_json={"paper_only": True},
            )
            self.db.add(position)
            await self.db.flush()
        position.contracts_count += fill_count
        position.average_entry_price = fill_price
        position.exposure_cents += fill_price * fill_count
        position.unrealized_pnl_cents = 0

    def _fill_price(self, reference_price: int) -> int:
        if self.fill_mode == PaperFillMode.AGGRESSIVE.value:
            return min(99, reference_price + max(1, int(reference_price * self.slippage_bps / 10_000)))
        if self.fill_mode == PaperFillMode.PASSIVE.value:
            return max(1, reference_price - max(1, int(reference_price * self.slippage_bps / 10_000)))
        return reference_price

    def _fill_count(self, requested_count: int, liquidity: int | None) -> int:
        if liquidity is None or liquidity >= requested_count * 10:
            return requested_count
        return max(1, int(requested_count * self.partial_fill_ratio))


class ReplayService:
    def __init__(self, db: AsyncSession, paper: PaperExecutionService) -> None:
        self.db = db
        self.paper = paper

    async def start(self, request: ReplayRequest) -> ReplayResult:
        run = SimulationRunRecord(
            name=request.name,
            mode="replay",
            status="running",
            market_ticker=request.market_ticker,
            started_at=datetime.now(timezone.utc),
            config_json=request.model_dump(mode="json"),
        )
        self.db.add(run)
        await self.db.flush()

        snapshot_query = select(MarketSnapshot).order_by(MarketSnapshot.observed_at.asc())
        if request.market_ticker:
            snapshot_query = snapshot_query.where(MarketSnapshot.market_ticker == request.market_ticker)
        if request.start_at:
            snapshot_query = snapshot_query.where(MarketSnapshot.observed_at >= request.start_at)
        if request.end_at:
            snapshot_query = snapshot_query.where(MarketSnapshot.observed_at <= request.end_at)
        snapshots = list((await self.db.execute(snapshot_query.limit(request.max_events))).scalars().all())

        signal_query = select(SignalRecord).order_by(SignalRecord.created_at.asc())
        if request.market_ticker:
            signal_query = signal_query.where(SignalRecord.market_ticker == request.market_ticker)
        if request.start_at:
            signal_query = signal_query.where(SignalRecord.created_at >= request.start_at)
        if request.end_at:
            signal_query = signal_query.where(SignalRecord.created_at <= request.end_at)
        signals = list((await self.db.execute(signal_query)).scalars().all())

        price_change = 0
        if len(snapshots) >= 2 and snapshots[0].last_price is not None and snapshots[-1].last_price is not None:
            price_change = snapshots[-1].last_price - snapshots[0].last_price
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.summary_json = {
            "processed_events": len(snapshots),
            "processed_signals": len(signals),
            "price_change_cents": price_change,
            "market_ticker": request.market_ticker,
        }
        await self.db.commit()
        return ReplayResult(
            run_id=run.id,
            status=run.status,
            processed_events=len(snapshots),
            processed_signals=len(signals),
            summary=run.summary_json,
        )
