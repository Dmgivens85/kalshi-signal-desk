from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MarketStatus(StrEnum):
    UNOPENED = "unopened"
    OPEN = "open"
    CLOSED = "closed"
    SETTLED = "settled"


class OrderStatus(StrEnum):
    RESTING = "resting"
    CANCELED = "canceled"
    EXECUTED = "executed"
    PENDING = "pending"


class OrderSide(StrEnum):
    YES = "yes"
    NO = "no"


class ClientOrderType(StrEnum):
    LIMIT = "limit"
    MARKET = "market"


class PaginationEnvelope(BaseModel):
    cursor: str = ""


class PriceRange(BaseModel):
    min_price: int
    max_price: int
    tick_size: int


class MveSelectedLeg(BaseModel):
    event_ticker: str | None = None
    market_ticker: str | None = None
    side: str | None = None


class Market(BaseModel):
    ticker: str
    event_ticker: str
    market_type: str
    title: str
    subtitle: str | None = None
    yes_sub_title: str | None = None
    no_sub_title: str | None = None
    created_time: datetime | None = None
    open_time: datetime | None = None
    close_time: datetime | None = None
    expected_expiration_time: datetime | None = None
    expiration_time: datetime | None = None
    latest_expiration_time: datetime | None = None
    settlement_timer_seconds: int | None = None
    status: str | None = None
    response_price_units: str | None = None
    yes_bid: float | int | None = None
    yes_bid_dollars: str | None = None
    yes_ask: float | int | None = None
    yes_ask_dollars: str | None = None
    last_price: int | None = None
    last_price_dollars: str | None = None
    previous_yes_bid_dollars: str | None = None
    previous_yes_ask: int | None = None
    previous_yes_ask_dollars: str | None = None
    previous_price: int | None = None
    previous_price_dollars: str | None = None
    volume: int | None = None
    open_interest: int | None = None
    liquidity: int | None = None
    liquidity_dollars: str | None = None
    settlement_value: int | None = None
    settlement_value_dollars: str | None = None
    expiration_value: str | None = None
    category: str | None = None
    risk_limit_cents: int | None = None
    fee_waiver_expiration_time: datetime | None = None
    early_close_condition: str | None = None
    tick_size: int | None = None
    strike_type: str | None = None
    floor_strike: float | None = None
    cap_strike: float | None = None
    functional_strike: str | None = None
    custom_strike: dict[str, Any] | None = None
    rules_primary: str | None = None
    rules_secondary: str | None = None
    mve_collection_ticker: str | None = None
    mve_selected_legs: list[MveSelectedLeg] | None = None
    price_level_structure: str | None = None
    price_ranges: list[PriceRange] | None = None


class GetMarketsResponse(PaginationEnvelope):
    markets: list[Market] = Field(default_factory=list)


class GetMarketResponse(BaseModel):
    market: Market


class Balance(BaseModel):
    balance: int | None = None
    portfolio_value: int | None = None
    available_balance: int | None = None
    balance_dollars: str | None = None
    portfolio_value_dollars: str | None = None
    available_balance_dollars: str | None = None


class GetBalanceResponse(BaseModel):
    balance: Balance


class Position(BaseModel):
    market_ticker: str
    position: int | None = None
    position_fp: Decimal | str | None = None
    fees_paid: int | None = None
    market_exposure: int | None = None
    resting_orders_count: int | None = None
    realized_pnl: int | None = None
    total_traded: int | None = None


class GetPositionsResponse(PaginationEnvelope):
    market_positions: list[Position] = Field(default_factory=list)


class Order(BaseModel):
    order_id: str | None = None
    client_order_id: str | None = None
    user_id: str | None = None
    market_ticker: str
    action: str | None = None
    side: str | None = None
    type: str | None = None
    status: str | None = None
    yes_price: int | None = None
    no_price: int | None = None
    count: int | None = None
    remaining_count: int | None = None
    filled_count: int | None = None
    queue_position: int | None = None
    taker_fees_dollars: str | None = None
    maker_fees_dollars: str | None = None
    expiration_time: datetime | None = None
    created_time: datetime | None = None
    last_update_time: datetime | None = None
    order_group_id: str | None = None
    cancel_order_on_pause: bool | None = None


class GetOrdersResponse(PaginationEnvelope):
    orders: list[Order] = Field(default_factory=list)


class CreateOrderRequest(BaseModel):
    action: str
    client_order_id: str | None = None
    count: int = Field(gt=0)
    side: OrderSide
    ticker: str
    type: ClientOrderType = ClientOrderType.LIMIT
    yes_price: int | None = Field(default=None, ge=1, le=99)
    no_price: int | None = Field(default=None, ge=1, le=99)
    expiration_ts: int | None = None
    buy_max_cost: int | None = None
    sell_position_floor: int | None = None
    cancel_order_on_pause: bool | None = None


class CreateOrderResponse(BaseModel):
    order: Order


class Fill(BaseModel):
    fill_id: str | None = None
    order_id: str | None = None
    market_ticker: str
    side: str | None = None
    action: str | None = None
    count: int | None = None
    price: int | None = None
    is_taker: bool | None = None
    created_time: datetime | None = None


class GetFillsResponse(PaginationEnvelope):
    fills: list[Fill] = Field(default_factory=list)


class QueuePosition(BaseModel):
    order_id: str
    market_ticker: str | None = None
    queue_position_fp: str


class QueuePositionsResponse(BaseModel):
    queue_positions: list[QueuePosition] = Field(default_factory=list)


class ExchangeStatus(BaseModel):
    exchange_active: bool | None = None
    trading_active: bool | None = None
    status: str | None = None
    close_time: datetime | None = None
    open_time: datetime | None = None


class WebSocketCommand(BaseModel):
    id: int
    cmd: str
    params: dict[str, Any]


class WebSocketSubscriptionResponse(BaseModel):
    id: int | None = None
    type: str
    msg: dict[str, Any] | None = None
    sid: int | None = None


class WebSocketMessage(BaseModel):
    type: str
    sid: int | None = None
    seq: int | None = None
    msg: dict[str, Any]


class WebSocketTickerMessage(BaseModel):
    type: str = "ticker"
    sid: int | None = None
    seq: int | None = None
    msg: dict[str, Any]


class WebSocketTradeMessage(BaseModel):
    type: str = "trade"
    sid: int | None = None
    seq: int | None = None
    msg: dict[str, Any]
