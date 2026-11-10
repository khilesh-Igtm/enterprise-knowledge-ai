from redis.asyncio import Redis

from app.core.config import settings


def create_redis_client() -> Redis:
    return Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
