from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChannelName(StrEnum):
    TICKER = "ticker"
    ORDERBOOK_DELTA = "orderbook_delta"
    ORDERBOOK_SNAPSHOT = "orderbook_snapshot"
    USER_ORDER = "user_order"
    USER_FILL = "fill"


class OrderSide(StrEnum):
    YES = "yes"
    NO = "no"


class ClientOrderType(StrEnum):
    LIMIT = "limit"
    MARKET = "market"


class OrderbookSideLevel(BaseModel):
    price: int
    quantity: int
    order_count: int | None = None


class SeriesModel(BaseModel):
    ticker: str
    title: str | None = None
    category: str | None = None
    frequency: str | None = None
    settlement_sources: list[str] = Field(default_factory=list)


class EventModel(BaseModel):
    ticker: str
    title: str
    subtitle: str | None = None
    category: str | None = None
    status: str | None = None
    series_ticker: str | None = None
    open_time: datetime | None = None
    close_time: datetime | None = None
    markets: list["MarketModel"] = Field(default_factory=list)


class MarketModel(BaseModel):
    ticker: str
    event_ticker: str
    series_ticker: str | None = None
    title: str
    subtitle: str | None = None
    market_type: str | None = None
    status: str | None = None
    yes_bid: int | None = None
    yes_ask: int | None = None
    last_price: int | None = None
    volume: int | None = None
    open_interest: int | None = None
    liquidity: int | None = None
    close_time: datetime | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class TickerUpdate(BaseModel):
    market_ticker: str
    event_ticker: str | None = None
    series_ticker: str | None = None
    yes_bid: int | None = None
    yes_ask: int | None = None
    yes_bid_dollars: Decimal | str | None = None
    yes_ask_dollars: Decimal | str | None = None
    last_price: int | None = None
    volume: int | None = None
    open_interest: int | None = None
    liquidity: int | None = None
    status: str | None = None
    time: datetime | None = None


class OrderbookSnapshot(BaseModel):
    market_ticker: str
    yes: list[OrderbookSideLevel] = Field(default_factory=list)
    no: list[OrderbookSideLevel] = Field(default_factory=list)
    ts: datetime | None = None

    @field_validator("yes", "no", mode="before")
    @classmethod
    def normalize_levels(cls, value: object) -> object:
        if isinstance(value, list):
            normalized: list[dict[str, int]] = []
            for item in value:
                if isinstance(item, dict):
                    normalized.append(item)
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    price, quantity = item[:2]
                    order_count = item[2] if len(item) > 2 else None
                    normalized.append(
                        {"price": int(price), "quantity": int(quantity), "order_count": order_count}
                    )
            return normalized
        return value


class OrderbookDelta(BaseModel):
    market_ticker: str
    price: int | None = None
    delta: int | None = None
    side: str | None = None
    client_order_id: str | None = None
    ts: datetime | None = None


class UserOrderUpdate(BaseModel):
    order_id: str | None = None
    client_order_id: str | None = None
    market_ticker: str | None = None
    status: str | None = None
    remaining_count: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class UserFillUpdate(BaseModel):
    fill_id: str | None = None
    order_id: str | None = None
    market_ticker: str | None = None
    price: int | None = None
    count: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class WebSocketEnvelope(BaseModel):
    type: str
    sid: int | None = None
    seq: int | None = None
    id: int | None = None
    msg: dict[str, Any] = Field(default_factory=dict)


class NormalizedMarketEvent(BaseModel):
    event_type: ChannelName | str
    market_ticker: str
    event_ticker: str | None = None
    series_ticker: str | None = None
    sequence_number: int | None = None
    subscription_id: int | None = None
    observed_at: datetime = Field(default_factory=utcnow)
    ticker_update: TickerUpdate | None = None
    orderbook_snapshot: OrderbookSnapshot | None = None
    orderbook_delta: OrderbookDelta | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)


class OrderbookResponse(BaseModel):
    orderbook: OrderbookSnapshot


class MultipleOrderbooksResponse(BaseModel):
    orderbooks: list[OrderbookSnapshot] = Field(default_factory=list)


class MarketsResponse(BaseModel):
    markets: list[MarketModel] = Field(default_factory=list)
    cursor: str = ""


class MarketResponse(BaseModel):
    market: MarketModel


class EventResponse(BaseModel):
    event: EventModel
    markets: list[MarketModel] = Field(default_factory=list)


class SeriesResponse(BaseModel):
    series: SeriesModel
    events: list[EventModel] = Field(default_factory=list)


class PositionModel(BaseModel):
    market_ticker: str
    position: int | None = None
    realized_pnl: int | None = None


class PositionsResponse(BaseModel):
    market_positions: list[PositionModel] = Field(default_factory=list)
    cursor: str = ""


class OrderModel(BaseModel):
    order_id: str | None = None
    client_order_id: str | None = None
    market_ticker: str
    side: str | None = None
    action: str | None = None
    status: str | None = None
    yes_price: int | None = None
    no_price: int | None = None
    count: int | None = None


class OrdersResponse(BaseModel):
    orders: list[OrderModel] = Field(default_factory=list)
    cursor: str = ""


class ExchangeStatus(BaseModel):
    exchange_active: bool | None = None
    trading_active: bool | None = None
    status: str | None = None
    close_time: datetime | None = None
    open_time: datetime | None = None


class CreateOrderRequest(BaseModel):
    ticker: str
    action: str
    side: OrderSide
    count: int = Field(gt=0)
    yes_price: int | None = Field(default=None, ge=1, le=99)
    no_price: int | None = Field(default=None, ge=1, le=99)
    client_order_id: str | None = None
    type: ClientOrderType = ClientOrderType.LIMIT
    time_in_force: str | None = None
    post_only: bool | None = None
    reduce_only: bool | None = None
    expiration_ts: int | None = None
    cancel_order_on_pause: bool | None = None


class CancelOrderResponse(BaseModel):
    order: OrderModel


class CreateOrderResponse(BaseModel):
    order: OrderModel


PlaceOrderRequest = CreateOrderRequest
PlaceOrderResponse = CreateOrderResponse
GetMarketResponse = MarketResponse
GetMarketsResponse = MarketsResponse
GetOrdersResponse = OrdersResponse
GetPositionsResponse = PositionsResponse


EventModel.model_rebuild()
