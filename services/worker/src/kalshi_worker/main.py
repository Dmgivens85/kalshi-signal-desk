from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from kalshi_common import PlatformSettings
from redis import Redis
from tenacity import retry, stop_after_attempt, wait_fixed


@retry(stop=stop_after_attempt(10), wait=wait_fixed(2))
def get_redis_client(url: str) -> Redis:
    client = Redis.from_url(url)
    client.ping()
    return client


def publish_heartbeat(client: Redis) -> None:
    payload = {
        "service": "worker",
        "status": "connected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    client.publish("platform.heartbeat", json.dumps(payload))


def main() -> None:
    settings = PlatformSettings()
    client = get_redis_client(settings.redis_url)

    while True:
        publish_heartbeat(client)
        time.sleep(10)


if __name__ == "__main__":
    main()
