from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy import text
from redis.asyncio import Redis
import websockets

from app.core.config import APISettings
from app.db.session import engine
from kalshi_client import KalshiHttpClient, build_kalshi_auth_headers
from kalshi_common import HealthCheckResult


async def get_readiness_report(settings: APISettings) -> dict[str, object]:
    checks: list[HealthCheckResult] = []

    try:
        async with engine.begin() as connection:
            await connection.execute(text("SELECT 1"))
        checks.append(HealthCheckResult(component="database", status="healthy"))
    except Exception as exc:
        checks.append(HealthCheckResult(component="database", status="unhealthy", detail=str(exc)))

    try:
        redis = Redis.from_url(settings.redis_url)
        await redis.ping()
        await redis.aclose()
        checks.append(HealthCheckResult(component="redis", status="healthy"))
    except Exception as exc:
        checks.append(HealthCheckResult(component="redis", status="unhealthy", detail=str(exc)))

    if settings.healthcheck_enable_externals:
        try:
            async with KalshiHttpClient(settings.build_kalshi_config()) as client:
                status = await client.get_exchange_status()
            checks.append(
                HealthCheckResult(
                    component="kalshi",
                    status="healthy",
                    detail=f"exchange_active={status.exchange_active}",
                )
            )
        except Exception as exc:
            checks.append(HealthCheckResult(component="kalshi", status="unhealthy", detail=str(exc)))

    overall = "healthy" if all(check.status == "healthy" for check in checks) else "degraded"
    return {
        "service": settings.app_name,
        "status": overall,
        "checks": [check.model_dump(mode="json") for check in checks],
    }


async def get_smoke_report(settings: APISettings) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    async def add_check(name: str, fn, *, critical: bool = True) -> None:
        try:
            detail = await fn()
            checks.append({"component": name, "status": "pass", "critical": critical, "detail": detail})
        except Exception as exc:
            checks.append({"component": name, "status": "fail", "critical": critical, "detail": str(exc)})

    await add_check("database", _check_database)
    await add_check("redis", lambda: _check_redis(settings))
    await add_check("migrations", _check_migrations)
    await add_check("mode_safety", lambda: _check_mode_safety(settings))
    await add_check("kill_switch", _check_kill_switch, critical=False)
    await add_check("automation_defaults", lambda: _check_automation_status(settings), critical=False)

    worker_urls = [
        ("market_stream", settings.market_stream_health_url),
        ("external_enrichment", settings.external_enrichment_health_url),
        ("signal_engine", settings.signal_engine_health_url),
        ("execution_engine", settings.execution_engine_health_url),
        ("notifier", settings.notifier_health_url),
        ("scheduler", settings.scheduler_health_url),
    ]
    for name, url in worker_urls:
        await add_check(name, lambda url=url, name=name: _check_worker_http(name, url), critical=False)

    if settings.smoke_test_enable_kalshi:
        await add_check("kalshi_config", lambda: _check_kalshi_config(settings))
        await add_check("kalshi_rest", lambda: _check_kalshi_rest(settings))
        await add_check("kalshi_websocket", lambda: _check_kalshi_websocket(settings), critical=False)

    failed_critical = [check for check in checks if check["critical"] and check["status"] != "pass"]
    overall = "pass" if not failed_critical else "fail"
    return {
        "service": settings.app_name,
        "status": overall,
        "rollback_recommended": bool(failed_critical),
        "checks": checks,
        "stale_stream_threshold_seconds": settings.build_kalshi_config().stale_after_seconds,
    }


async def _check_database() -> str:
    async with engine.begin() as connection:
        await connection.execute(text("SELECT 1"))
    return "database reachable"


async def _check_redis(settings: APISettings) -> str:
    redis = Redis.from_url(settings.redis_url)
    try:
        await redis.ping()
    finally:
        await redis.aclose()
    return "redis reachable"


async def _check_migrations() -> str:
    async with engine.begin() as connection:
        result = await connection.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar_one_or_none()
    if not version:
        raise RuntimeError("alembic_version table is empty")
    return f"migration head present: {version}"


async def _check_mode_safety(settings: APISettings) -> str:
    mode = settings.resolved_execution_mode
    if settings.app_env.lower() == "staging" and mode == "live":
        raise RuntimeError("staging must not run in live mode")
    if settings.app_env.lower() == "production" and mode == "live" and not settings.live_trading_enabled:
        raise RuntimeError("production reports live requested but live confirmation gate is closed")
    return f"execution_mode={mode} live_trading_enabled={settings.live_trading_enabled}"


async def _check_kill_switch() -> str:
    async with engine.begin() as connection:
        result = await connection.execute(
            text("SELECT enabled, reason FROM system_controls WHERE id = 'global_kill_switch'")
        )
        row = result.first()
    if row is None:
        return "kill switch record not initialized"
    return f"enabled={bool(row[0])} reason={row[1] or 'none'}"


async def _check_automation_status(settings: APISettings) -> str:
    mode = settings.resolved_execution_mode
    return f"automation endpoint available; current execution_mode={mode}"


async def _check_worker_http(name: str, url: str | None) -> str:
    if not url:
        raise RuntimeError(f"{name} health url not configured")
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)
    if response.status_code != 200:
        raise RuntimeError(f"{name} unhealthy: {response.status_code}")
    return f"{name} healthy via {url}"


async def _check_kalshi_config(settings: APISettings) -> str:
    config = settings.build_kalshi_config()
    config.require_credentials()
    return f"credentials loaded for {config.environment.value}"


async def _check_kalshi_rest(settings: APISettings) -> str:
    async with KalshiHttpClient(settings.build_kalshi_config()) as client:
        status = await client.get_exchange_status()
    return f"exchange_active={status.exchange_active}"


async def _check_kalshi_websocket(settings: APISettings) -> str:
    config = settings.build_kalshi_config()
    headers = build_kalshi_auth_headers(config, "GET", "/trade-api/ws/v2")
    async with websockets.connect(
        config.resolved_ws_url,
        additional_headers=headers,
        open_timeout=min(config.connect_timeout_seconds, 5.0),
        ping_interval=None,
        close_timeout=2,
    ) as connection:
        await connection.close()
    return "websocket handshake succeeded"
