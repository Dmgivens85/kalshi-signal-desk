from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_settings, get_db_session, get_kalshi_client, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings
from app.services.execution import ExecutionError, GuardedExecutionService
from kalshi_client import CreateOrderRequest, KalshiHttpClient

router = APIRouter()


class KillSwitchUpdateRequest(BaseModel):
    enabled: bool
    reason: str | None = None


def get_execution_service(
    settings: APISettings,
    db: AsyncSession,
    kalshi: KalshiHttpClient,
) -> GuardedExecutionService:
    return GuardedExecutionService(settings, db, kalshi)


@router.get("/kill-switch")
async def get_kill_switch(
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    return (await service.get_kill_switch()).to_dict()


@router.put("/kill-switch")
async def update_kill_switch(
    payload: KillSwitchUpdateRequest,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    return await service.set_kill_switch(enabled=payload.enabled, reason=payload.reason, actor_user_id=context.subject)


@router.post("/preview")
async def preview_order_execution(
    payload: CreateOrderRequest,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    order = await service.create_preview_record(payload, context)
    return order.to_dict()


@router.post("/{order_id}/approve")
async def approve_execution(
    order_id: str,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    try:
        order = await service.approve_order(order_id, context)
    except ExecutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return order.to_dict()


@router.post("/{order_id}/execute")
async def execute_approved_order(
    order_id: str,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    try:
        return await service.execute_order(order_id, context)
    except ExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/audit")
async def list_execution_audit(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    return await service.list_audit_logs()
