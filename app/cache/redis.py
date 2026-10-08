import redis
from redis.asyncio import Redis

from app.config.settings import settings


class RedisCache:

    def __init__(self):

        print(f"REDIS_URL = {settings.redis_url!r}")

        self.redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )


    async def get(
        self,
        key: str,
    ) -> str | None:

        try:
            return await self.redis.get(key)
        except (redis.ConnectionError, redis.TimeoutError):
            # Если Redis не работает, просто возвращаем None, 
            # чтобы бот продолжал работу и делал прямые запросы
            return None


    async def set(
        self,
            key: str,
            value: str,
            expire: int = 3600,
        ) -> None:
            try:
                await self.redis.set(
                    key,
                    value,
                    ex=expire,
                )
            except (redis.ConnectionError, redis.TimeoutError):
                # Если Redis не работает, просто молча пропускаем сохранение.
                # Бот продолжит работать, а данные просто не закешируются в этот раз.
                pass

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