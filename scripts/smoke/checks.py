from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .config import SmokeConfig


@dataclass(slots=True)
class CheckResult:
    subsystem: str
    ok: bool
    reason: str
    next_step: str
    critical: bool = True


async def run_checks(config: SmokeConfig) -> list[CheckResult]:
    results: list[CheckResult] = []
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        results.extend(await _web_checks(client, config))
        results.extend(await _api_checks(client, config))
    return results


async def _web_checks(client: httpx.AsyncClient, config: SmokeConfig) -> list[CheckResult]:
    results: list[CheckResult] = []
    homepage = await _safe_get(client, f"{config.web_url}/")
    results.append(
        _result(
            "web_home",
            homepage is not None and homepage.status_code == 200,
            f"homepage returned {homepage.status_code}" if homepage is not None else "web connection failed",
            "Check ALB/web task logs and Next.js startup.",
        )
    )

    app_route = await _safe_get(client, f"{config.web_url}/paper")
    results.append(
        _result(
            "web_route",
            app_route is not None and app_route.status_code == 200,
            f"/paper returned {app_route.status_code}" if app_route is not None else "route connection failed",
            "Check app routing and server render errors.",
        )
    )

    if config.require_manifest:
        manifest = await _safe_get(client, f"{config.web_url}/manifest.webmanifest")
        if manifest is not None and manifest.status_code == 404:
            manifest = await _safe_get(client, f"{config.web_url}/manifest.json")
        results.append(
            _result(
                "pwa_manifest",
                manifest is not None and manifest.status_code == 200,
                f"manifest returned {manifest.status_code}" if manifest is not None else "manifest connection failed",
                "Check manifest route and static asset generation.",
                critical=False,
            )
        )
    return results


async def _api_checks(client: httpx.AsyncClient, config: SmokeConfig) -> list[CheckResult]:
    results: list[CheckResult] = []
    headers = {"Authorization": f"Bearer {config.auth_token}"} if config.auth_token else {}

    live = await _safe_get(client, f"{config.api_url}/api/health")
    results.append(
        _result(
            "api_health",
            live is not None and live.status_code == 200,
            f"/api/health returned {live.status_code}" if live is not None else "api connection failed",
            "Inspect API task health and CloudWatch logs.",
        )
    )

    ready = await _safe_get(client, f"{config.api_url}/api/health/ready")
    ready_ok = ready is not None and ready.status_code == 200 and ready.json().get("status") in {"healthy", "degraded"}
    results.append(
        _result(
            "api_ready",
            ready_ok,
            f"/api/health/ready returned {ready.status_code}" if ready is not None else "api readiness connection failed",
            "Check DB/Redis readiness and startup configuration.",
        )
    )

    smoke = await _safe_get(client, f"{config.api_url}/api/health/smoke", headers=headers)
    if smoke is None or smoke.status_code != 200:
        results.append(
            CheckResult(
                subsystem="deployment_smoke",
                ok=False,
                reason=f"/api/health/smoke returned {smoke.status_code}" if smoke is not None else "smoke endpoint connection failed",
                next_step="Check API auth token, deployment health route, and service dependencies.",
            )
        )
        return results

    payload = smoke.json()
    rollback = bool(payload.get("rollback_recommended"))
    for item in payload.get("checks", []):
        name = str(item.get("component"))
        detail = str(item.get("detail"))
        status = item.get("status") == "pass"
        critical = bool(item.get("critical", True))
        if name == "kalshi_rest" and not config.require_kalshi:
            critical = False
        next_step = _next_step_for(name)
        results.append(CheckResult(name, status, detail, next_step, critical=critical))

    markets = await _safe_get(client, f"{config.api_url}/api/markets")
    market_ok = markets is not None and markets.status_code == 200
    results.append(
        _result(
            "db_backed_endpoint",
            market_ok,
            f"/api/markets returned {markets.status_code}" if markets is not None else "market endpoint connection failed",
            "Check database seed/state and market read path.",
        )
    )

    notifications = await _safe_get(client, f"{config.api_url}/api/notifications/health", headers=headers)
    results.append(
        _result(
            "notifications_api",
            notifications is not None and notifications.status_code == 200,
            f"/api/notifications/health returned {notifications.status_code}" if notifications is not None else "notification endpoint connection failed",
            "Check notifier config, DB access, and protected route auth.",
            critical=False,
        )
    )

    automation = await _safe_get(client, f"{config.api_url}/api/automation/status", headers=headers)
    results.append(
        _result(
            "automation_api",
            automation is not None and automation.status_code == 200,
            f"/api/automation/status returned {automation.status_code}" if automation is not None else "automation endpoint connection failed",
            "Check automation service routing and auth token.",
            critical=False,
        )
    )

    kill_switch = await _safe_get(client, f"{config.api_url}/api/execution/kill-switch", headers=headers)
    results.append(
        _result(
            "kill_switch_api",
            kill_switch is not None and kill_switch.status_code == 200,
            f"/api/execution/kill-switch returned {kill_switch.status_code}" if kill_switch is not None else "kill-switch endpoint connection failed",
            "Check execution API routing, DB access, and auth token.",
            critical=False,
        )
    )

    paper = await _safe_get(client, f"{config.api_url}/api/paper/status", headers=headers)
    if paper.status_code == 200:
        mode = str(paper.json().get("mode"))
        mode_ok = True
        if config.expected_mode:
            mode_ok = mode == config.expected_mode
        if not config.allow_live and mode == "live":
            mode_ok = False
        results.append(
            _result(
                "mode_boundary",
                mode_ok,
                f"reported mode={mode}",
                "Disable execution immediately if the reported mode is unexpected.",
            )
        )
    else:
        results.append(
            CheckResult(
                "mode_boundary",
                False,
                f"/api/paper/status returned {paper.status_code}",
                "Check execution service wiring and auth.",
            )
        )

    if rollback:
        results.append(
            CheckResult(
                "rollback_signal",
                False,
                "Critical deployment smoke checks failed.",
                "Keep traffic on the previous version or roll back this service revision.",
                critical=True,
            )
        )
    return results


async def _safe_get(client: httpx.AsyncClient, url: str, headers: dict[str, str] | None = None) -> httpx.Response | None:
    try:
        return await client.get(url, headers=headers)
    except httpx.HTTPError:
        return None


def _result(subsystem: str, ok: bool, reason: str, next_step: str, critical: bool = True) -> CheckResult:
    return CheckResult(subsystem=subsystem, ok=ok, reason=reason, next_step=next_step, critical=critical)


def _next_step_for(name: str) -> str:
    mapping: dict[str, str] = {
        "database": "Check RDS connectivity, credentials, and migration task status.",
        "redis": "Check ElastiCache connectivity and task security groups.",
        "migrations": "Verify the one-off migration task ran successfully against this environment.",
        "kalshi_config": "Verify Kalshi credentials and environment-specific secret wiring.",
        "kalshi_rest": "Check outbound networking, Kalshi credentials, and REST auth headers.",
        "kalshi_websocket": "Check outbound websocket access and Kalshi websocket auth.",
        "market_stream": "Inspect market-stream task health and websocket logs.",
        "external_enrichment": "Inspect external-enrichment task health and provider connectivity.",
        "signal_engine": "Inspect signal-engine task health and DB access.",
        "execution_engine": "Inspect execution-engine task health and automation loop logs.",
        "notifier": "Inspect notifier task health and provider configuration.",
        "scheduler": "Inspect scheduler task health and periodic job loop.",
        "mode_safety": "Review execution-mode env vars and confirm live gates are closed.",
        "kill_switch": "Review kill-switch state and recent execution/risk events.",
        "automation_defaults": "Review automation policy defaults and pause/disable state.",
        "notification_health": "Review notification provider config and delivery audit logs.",
    }
    return mapping.get(name, "Inspect the owning service logs and deployment config.")


def summarize(results: list[CheckResult]) -> dict[str, Any]:
    failed = [item for item in results if not item.ok]
    critical_failed = [item for item in failed if item.critical]
    return {
        "status": "PASS" if not critical_failed else "FAIL",
        "failed": len(failed),
        "critical_failed": len(critical_failed),
        "rollback_recommended": bool(critical_failed),
    }
