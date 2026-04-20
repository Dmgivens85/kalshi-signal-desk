from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_settings, get_db_session, get_kalshi_client, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings
from app.services.automation import AutomationService
from execution_engine.automation.models import AutomationPolicyInput
from kalshi_client import KalshiHttpClient

router = APIRouter()


class ReasonPayload(BaseModel):
    reason: str | None = None


class PausePayload(BaseModel):
    reason: str = Field(min_length=3)


def get_service(settings: APISettings, db: AsyncSession, kalshi: KalshiHttpClient) -> AutomationService:
    return AutomationService(settings, db, kalshi)


@router.get("/status")
async def get_status(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).status()


@router.get("/policies")
async def list_policies(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).list_policies()


@router.put("/policies")
async def upsert_policy(
    payload: AutomationPolicyInput,
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).upsert_policy(payload)


@router.post("/enable")
async def enable_automation(
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).enable(context.subject)


@router.post("/disable")
async def disable_automation(
    payload: ReasonPayload | None = None,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).disable(context.subject, payload.reason if payload else None)


@router.post("/pause")
async def pause_automation(
    payload: PausePayload,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).pause(context.subject, payload.reason)


@router.post("/resume")
async def resume_automation(
    payload: ReasonPayload | None = None,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).resume(context.subject, payload.reason if payload else None)


@router.get("/events")
async def list_events(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).list_events()


@router.get("/failures")
async def list_failures(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).list_failures()


@router.post("/evaluate")
async def evaluate_automation_once(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_service(settings, db, kalshi).evaluate_once()
