from fastapi import FastAPI

from api_shell.api.router import api_router
from api_shell.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Kalshi Signal Desk API Shell",
    version="0.1.0",
    summary="Future-facing FastAPI app shell for Kalshi Signal Desk.",
)
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "docs": "/docs",
    }
