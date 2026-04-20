from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_settings, get_db_session, get_kalshi_client, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings
from app.services.execution import ExecutionError, GuardedExecutionService
from execution_engine.paper.models import ReplayRequest
from kalshi_client import KalshiHttpClient

router = APIRouter()


class ReasonPayload(BaseModel):
    reason: str | None = None


class ReplayStartPayload(BaseModel):
    name: str
    market_ticker: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    max_events: int = Field(default=500, gt=0, le=5000)


def get_service(settings: APISettings, db: AsyncSession, kalshi: KalshiHttpClient) -> GuardedExecutionService:
    return GuardedExecutionService(settings, db, kalshi)


@router.get("/status")
async def get_paper_status(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).paper_status()


@router.post("/enable")
async def enable_paper_mode(
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).set_execution_mode("paper", context.subject)


@router.post("/disable")
async def disable_execution(
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).set_execution_mode("disabled", context.subject)


@router.get("/orders")
async def list_paper_orders(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).list_paper_orders()


@router.get("/orders/{paper_order_id}")
async def get_paper_order(
    paper_order_id: str,
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_service(settings, db, kalshi)
    try:
        return await service.get_paper_order(paper_order_id)
    except ExecutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/positions")
async def list_paper_positions(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).list_paper_positions()


@router.get("/performance")
async def get_paper_performance(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).paper_performance()


@router.post("/replay/start")
async def start_replay(
    payload: ReplayStartPayload,
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_service(settings, db, kalshi)
    return await service.start_replay(
        ReplayRequest(
            name=payload.name,
            market_ticker=payload.market_ticker,
            start_at=payload.start_at,
            end_at=payload.end_at,
            max_events=payload.max_events,
        )
    )


@router.get("/replay/{run_id}")
async def get_replay_run(
    run_id: str,
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_service(settings, db, kalshi)
    try:
        return await service.get_replay(run_id)
    except ExecutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/simulation-runs")
async def list_simulation_runs(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).list_simulation_runs()
