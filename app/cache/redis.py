from redis.asyncio import Redis

from app.config.settings import settings


class RedisCache:

    def __init__(self):

        self.redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )


    async def get(
        self,
        key: str,
    ) -> str | None:

        return await self.redis.get(
            key
        )


    async def set(
        self,
        key: str,
        value: str,
        expire: int = 3600,
    ) -> None:

        await self.redis.set(
            key,
            value,
            ex=expire,
        )


    async def delete(
        self,
        key: str,
    ) -> None:

        await self.redis.delete(
            key
        )


    async def close(
        self,
    ) -> None:

        await self.redis.aclose()



redis_cache = RedisCache()