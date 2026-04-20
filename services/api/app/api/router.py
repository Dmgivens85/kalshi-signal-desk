from fastapi import APIRouter

from app.api.routes import approvals, auth, automation, enrichments, execution, health, markets, notifications, orders, paper, positions, risk, signals, watchlist

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(markets.router, prefix="/markets", tags=["markets"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(enrichments.router, prefix="/enrichments", tags=["enrichments"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])
api_router.include_router(paper.router, prefix="/paper", tags=["paper"])
api_router.include_router(positions.router, prefix="/positions", tags=["positions"])
api_router.include_router(execution.router, prefix="/execution", tags=["execution"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
