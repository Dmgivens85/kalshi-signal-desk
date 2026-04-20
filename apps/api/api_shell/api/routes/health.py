from fastapi import APIRouter
from pydantic import BaseModel

from api_shell.core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    service: str
    status: str
    environment: str


@router.get("", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        service=settings.app_name,
        status="healthy",
        environment=settings.app_env,
    )
