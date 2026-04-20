from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_api_settings, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings

router = APIRouter()


class SessionResponse(BaseModel):
    subject: str
    email: str | None = None
    role: str
    auth_mode: str
    anonymous: bool = False


@router.get("/session", response_model=SessionResponse)
async def get_session(
    context: AuthContext = Depends(require_auth),
    settings: APISettings = Depends(get_api_settings),
) -> SessionResponse:
    return SessionResponse(
        subject=context.subject,
        email=context.email,
        role=context.role,
        auth_mode=settings.auth_mode,
        anonymous=context.is_anonymous,
    )


@router.get("/me", response_model=SessionResponse)
async def get_me(context: AuthContext = Depends(require_auth), settings: APISettings = Depends(get_api_settings)) -> SessionResponse:
    return SessionResponse(
        subject=context.subject,
        email=context.email,
        role=context.role,
        auth_mode=settings.auth_mode,
        anonymous=context.is_anonymous,
    )
