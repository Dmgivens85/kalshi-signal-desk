from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import HTTPException, status

from app.core.config import APISettings


@dataclass(slots=True)
class AuthContext:
    subject: str
    role: str
    email: str | None = None
    is_anonymous: bool = False

    @classmethod
    def anonymous(cls) -> "AuthContext":
        return cls(subject="anonymous", role="anonymous", is_anonymous=True)


def decode_bearer_token(token: str, settings: APISettings) -> AuthContext:
    if settings.dev_auth_token and token == settings.dev_auth_token:
        return AuthContext(subject="dev-user", role="admin", email="dev@local")

    if not settings.app_jwt_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT auth is not configured")

    try:
        payload = jwt.decode(token, settings.app_jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token") from exc

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    return AuthContext(
        subject=subject,
        role=payload.get("role", "analyst"),
        email=payload.get("email"),
    )
