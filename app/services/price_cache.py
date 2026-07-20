import json

from redis.asyncio import Redis

from app.config.settings import settings


class PriceCache:

    def __init__(self):

        self.redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )


    async def close(self):

        await self.redis.close()



    def _key(
        self,
        origin: str,
        destination: str,
        departure_date: str,
    ) -> str:

        return (
            f"price:"
            f"{origin}:"
            f"{destination}:"
            f"{departure_date}"
        )



    async def get(
        self,
        origin: str,
        destination: str,
        departure_date: str,
    ) -> dict | None:

        key = self._key(
            origin,
            destination,
            departure_date,
        )

        data = await self.redis.get(key)

        if data is None:
            return None

        return json.loads(data)



    async def set(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        data: dict,
        expire: int = 3600,
    ) -> None:

        key = self._key(
            origin,
            destination,
            departure_date,
        )

        await self.redis.set(
            key,
            json.dumps(data),
            ex=expire,
        )
