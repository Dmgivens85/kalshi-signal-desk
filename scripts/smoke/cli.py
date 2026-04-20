from __future__ import annotations

import argparse
import asyncio
import sys

from .checks import run_checks, summarize
from .config import SmokeConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kalshi Signal Desk deployment smoke tests")
    parser.add_argument("--env", choices=["local", "staging", "production"], help="Target environment label")
    parser.add_argument("--web-url", help="Base URL for the web app")
    parser.add_argument("--api-url", help="Base URL for the API")
    parser.add_argument("--auth-token", help="Bearer token for protected smoke endpoints")
    parser.add_argument("--expected-mode", choices=["disabled", "paper", "live"], help="Expected execution mode")
    parser.add_argument("--allow-live", action="store_true", help="Allow live mode without failing smoke tests")
    parser.add_argument("--skip-kalshi", action="store_true", help="Do not require Kalshi connectivity checks")
    return parser


async def _main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = SmokeConfig.from_env()
    if args.env:
        config.environment = args.env
    if args.web_url:
        config.web_url = args.web_url
    if args.api_url:
        config.api_url = args.api_url
    if args.auth_token:
        config.auth_token = args.auth_token
    if args.expected_mode:
        config.expected_mode = args.expected_mode
    if args.allow_live:
        config.allow_live = True
    if args.skip_kalshi:
        config.require_kalshi = False

    results = await run_checks(config)
    summary = summarize(results)

    print(f"Smoke test environment: {config.environment}")
    for item in results:
        marker = "PASS" if item.ok else "FAIL"
        print(f"[{marker}] {item.subsystem}: {item.reason}")
        if not item.ok:
            print(f"       next: {item.next_step}")

    print(
        f"Overall: {summary['status']} | failed={summary['failed']} | "
        f"critical_failed={summary['critical_failed']} | "
        f"rollback_recommended={summary['rollback_recommended']}"
    )
    return 0 if summary["status"] == "PASS" else 1


def main() -> None:
    raise SystemExit(asyncio.run(_main()))


if __name__ == "__main__":
    main()
