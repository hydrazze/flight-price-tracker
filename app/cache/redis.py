from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

from app.config.settings import settings


class RedisCache:
    def __init__(self):
        self.redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )

    async def get(self, key: str) -> str | None:
        try:
            return await self.redis.get(key)
        except (ConnectionError, TimeoutError):
            return None

    async def set(self, key: str, value: str, expire: int = 3600) -> None:
        try:
            await self.redis.set(key, value, ex=expire)
        except (ConnectionError, TimeoutError):
            pass

    async def delete(self, key: str) -> None:
        try:
            await self.redis.delete(key)
        except (ConnectionError, TimeoutError):
            pass

    async def close(self) -> None:
        await self.redis.aclose()


redis_cache = RedisCache()
