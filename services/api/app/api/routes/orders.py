from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_settings, get_db_session, get_kalshi_client, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings
from app.services.execution import ExecutionError, GuardedExecutionService
from kalshi_client import CreateOrderRequest, KalshiHttpClient

router = APIRouter()


class OrderPreviewPayload(BaseModel):
    signal_id: str | None = None
    signal_summary: str | None = None
    overnight_flag: bool = False
    confidence_score: float | None = None
    order: CreateOrderRequest | None = None


class ApprovalActionPayload(BaseModel):
    notes: str | None = None


def get_execution_service(
    settings: APISettings,
    db: AsyncSession,
    kalshi: KalshiHttpClient,
) -> GuardedExecutionService:
    return GuardedExecutionService(settings, db, kalshi)


@router.get("")
async def list_orders(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    return await service.list_orders()


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    try:
        return (await service.get_order(order_id)).to_dict()
    except ExecutionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/preview")
async def preview_order(
    payload: OrderPreviewPayload,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    try:
        if payload.signal_id and payload.order is None:
            order = await service.create_preview_from_signal(payload.signal_id, context)
        elif payload.order is not None:
            order = await service.create_preview_record(
                payload.order,
                context,
                signal_id=payload.signal_id,
                signal_summary=payload.signal_summary,
                overnight_flag=payload.overnight_flag,
                confidence_score=payload.confidence_score,
            )
        else:
            raise HTTPException(status_code=422, detail="Either signal_id or order payload is required.")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return order.to_dict()


@router.post("/{order_id}/approve")
async def approve_order(
    order_id: str,
    payload: ApprovalActionPayload | None = None,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    try:
        return (await service.approve_order(order_id, context, payload.notes if payload else None)).to_dict()
    except ExecutionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{order_id}/reject")
async def reject_order(
    order_id: str,
    payload: ApprovalActionPayload | None = None,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = get_execution_service(settings, db, kalshi)
    try:
        return (await service.reject_order(order_id, context, payload.notes if payload else None)).to_dict()
    except ExecutionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{order_id}/submit")
async def submit_order(
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
        raise HTTPException(status_code=409, detail=str(exc)) from exc
