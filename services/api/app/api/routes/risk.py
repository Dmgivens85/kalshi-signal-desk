from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_settings, get_db_session, get_kalshi_client, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings
from app.db.models import RiskLimit
from app.services.execution import GuardedExecutionService
from kalshi_client import KalshiHttpClient

router = APIRouter()


class RiskLimitUpsert(BaseModel):
    name: str = "default"
    max_order_count: int = Field(default=100, gt=0)
    max_order_notional_cents: int = Field(default=10_000, gt=0)
    max_daily_notional_cents: int = Field(default=100_000, gt=0)
    max_exposure_per_market_cents: int = Field(default=25_000, gt=0)
    max_exposure_per_category_cents: int = Field(default=75_000, gt=0)
    max_simultaneous_positions: int = Field(default=8, gt=0)
    max_spread_cents: int = Field(default=12, gt=0)
    min_liquidity: int = Field(default=100, ge=0)
    max_category_concentration: float = Field(default=0.55, ge=0, le=1)
    cooldown_after_loss_minutes: int = Field(default=90, ge=0)
    min_time_to_resolution_minutes: int = Field(default=60, ge=0)
    overnight_max_spread_cents: int = Field(default=8, gt=0)
    overnight_min_liquidity: int = Field(default=250, ge=0)
    allowed_markets: list[str] = Field(default_factory=list)


class KillSwitchUpdateRequest(BaseModel):
    enabled: bool
    reason: str | None = None


@router.get("")
async def get_risk_status(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = GuardedExecutionService(settings, db, kalshi)
    return await service.risk_summary()


@router.put("")
async def upsert_risk_limit(
    payload: RiskLimitUpsert,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    result = await db.execute(select(RiskLimit).where(RiskLimit.name == payload.name))
    risk_limit = result.scalar_one_or_none()

    if risk_limit is None:
        risk_limit = RiskLimit(
            user_id=context.subject if context.subject != "anonymous" else None,
            name=payload.name,
        )
        db.add(risk_limit)

    for key, value in payload.model_dump().items():
        setattr(risk_limit, key, value)

    await db.commit()
    await db.refresh(risk_limit)
    return risk_limit.to_dict()


@router.post("/kill-switch")
async def update_kill_switch(
    payload: KillSwitchUpdateRequest,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = GuardedExecutionService(settings, db, kalshi)
    return await service.set_kill_switch(enabled=payload.enabled, reason=payload.reason, actor_user_id=context.subject)
