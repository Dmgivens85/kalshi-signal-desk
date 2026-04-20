from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext, decode_bearer_token
from app.core.config import APISettings, get_settings
from app.db.session import get_async_session
from app.integrations.kalshi import get_kalshi_client

security = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_async_session():
        yield session


def get_api_settings() -> APISettings:
    return get_settings()


async def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: APISettings = Depends(get_api_settings),
) -> AuthContext:
    if credentials is None:
        if settings.auth_optional:
            return AuthContext.anonymous()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    return decode_bearer_token(credentials.credentials, settings)


async def require_auth(
    context: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    if context.is_anonymous:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return context


__all__ = ["get_api_settings", "get_auth_context", "get_db_session", "get_kalshi_client", "require_auth"]
