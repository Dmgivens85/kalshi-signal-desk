from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_settings, get_db_session, get_kalshi_client, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings
from app.services.execution import GuardedExecutionService
from kalshi_client import KalshiHttpClient

router = APIRouter()


@router.get("/pending")
async def list_pending_approvals(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    kalshi: KalshiHttpClient = Depends(get_kalshi_client),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = GuardedExecutionService(settings, db, kalshi)
    return await service.list_pending_approvals()
