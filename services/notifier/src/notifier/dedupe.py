from __future__ import annotations

from datetime import datetime, timedelta, timezone

from redis.exceptions import RedisError
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationDeliveryRecord


class DedupeStore:
    def __init__(self, redis_client: Redis | None = None) -> None:
        self.redis = redis_client

    async def check_and_mark(self, db: AsyncSession, dedupe_key: str, ttl_seconds: int) -> bool:
        if self.redis is not None:
            try:
                created = await self.redis.set(f"notify:{dedupe_key}", "1", ex=ttl_seconds, nx=True)
                if created:
                    return False
                return True
            except RedisError:
                # Fall back to the durable database path when Redis is unavailable in local dev.
                pass

        cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
        result = await db.execute(
            select(NotificationDeliveryRecord).where(
                NotificationDeliveryRecord.dedupe_key == dedupe_key,
                NotificationDeliveryRecord.created_at >= cutoff,
                NotificationDeliveryRecord.status.in_(["sent", "suppressed_duplicate"]),
            )
        )
        return result.scalar_one_or_none() is not None
