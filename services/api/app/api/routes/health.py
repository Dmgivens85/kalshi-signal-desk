from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_api_settings, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings
from app.services.health import get_readiness_report, get_smoke_report

router = APIRouter()


class LivenessResponse(BaseModel):
    service: str
    status: str
    version: str


@router.get("/live", response_model=LivenessResponse)
async def live(settings: APISettings = Depends(get_api_settings)) -> LivenessResponse:
    return LivenessResponse(service=settings.app_name, status="healthy", version=settings.app_version)


@router.get("", response_model=LivenessResponse)
async def health(settings: APISettings = Depends(get_api_settings)) -> LivenessResponse:
    return LivenessResponse(service=settings.app_name, status="healthy", version=settings.app_version)


@router.get("/ready")
async def ready(settings: APISettings = Depends(get_api_settings)) -> dict[str, object]:
    return await get_readiness_report(settings)


@router.get("/smoke")
async def smoke(
    _: AuthContext = Depends(require_auth),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    return await get_smoke_report(settings)
