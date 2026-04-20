from __future__ import annotations

from datetime import datetime, timezone

from app.db.models import KalshiMarket, MarketSnapshot, OrderbookEvent

from signal_engine.models import KalshiFeatureSet


def _safe_ratio(value: float, denominator: float) -> float:
    return value / denominator if denominator else 0.0


def build_kalshi_features(
    market: KalshiMarket,
    snapshots: list[MarketSnapshot],
    orderbook_events: list[OrderbookEvent],
) -> KalshiFeatureSet:
    latest_price = (market.last_price or market.yes_bid or market.yes_ask or 50) / 100.0
    first_price = ((snapshots[0].last_price if snapshots else market.last_price) or 50) / 100.0
    last_snapshot_price = ((snapshots[-1].last_price if snapshots else market.last_price) or 50) / 100.0
    short_term_momentum = max(-1.0, min(1.0, (last_snapshot_price - first_price) / 0.15))
    move_size = abs(last_snapshot_price - first_price)
    spread_width = _safe_ratio(((market.yes_ask or 50) - (market.yes_bid or 50)), 100.0)

    liquidity_basis = float((market.liquidity or 0) + (market.volume or 0))
    liquidity_depth_score = max(0.0, min(1.0, liquidity_basis / 25000.0))

    latest_orderbook = next((item for item in reversed(orderbook_events) if item.event_type == "orderbook_snapshot"), None)
    if latest_orderbook is not None:
        bid_depth = sum(level.get("quantity", 0) for level in latest_orderbook.bid_levels)
        ask_depth = sum(level.get("quantity", 0) for level in latest_orderbook.ask_levels)
        orderbook_imbalance = _safe_ratio((bid_depth - ask_depth), max(1.0, bid_depth + ask_depth))
    else:
        orderbook_imbalance = 0.0

    price_changes = []
    previous = None
    for snapshot in snapshots:
        current = (snapshot.last_price or 50) / 100.0
        if previous is not None:
            price_changes.append(abs(current - previous))
        previous = current
    volatility_proxy = max(0.0, min(1.0, sum(price_changes) / max(0.01, len(price_changes) * 0.08))) if price_changes else 0.0

    if market.close_time is not None:
        now = datetime.now(timezone.utc)
        close_time = market.close_time
        if close_time.tzinfo is None:
            close_time = close_time.replace(tzinfo=timezone.utc)
        hours_to_close = max(0.0, (close_time - now).total_seconds() / 3600.0)
        time_to_resolution_factor = max(0.0, min(1.0, 1.0 - min(1.0, hours_to_close / 168.0)))
    else:
        time_to_resolution_factor = 0.25

    unusual_activity_basis = _safe_ratio(float(len(orderbook_events)), 20.0) + _safe_ratio(float(market.volume or 0), 15000.0)
    unusual_activity_score = max(0.0, min(1.0, unusual_activity_basis / 2.0))

    return KalshiFeatureSet(
        short_term_momentum=round(short_term_momentum, 6),
        move_size=round(move_size, 6),
        spread_width=round(spread_width, 6),
        liquidity_depth_score=round(liquidity_depth_score, 6),
        orderbook_imbalance=round(orderbook_imbalance, 6),
        volatility_proxy=round(volatility_proxy, 6),
        time_to_resolution_factor=round(time_to_resolution_factor, 6),
        unusual_activity_score=round(unusual_activity_score, 6),
    )
