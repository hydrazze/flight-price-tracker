from datetime import date
import asyncio
import json

import httpx

from app.config.settings import settings
from app.schemas.travelpayouts import PricesForDatesResponse

from app.logging.logger import logger
from app.cache.redis import redis_cache


class TravelPayoutsClient:

    BASE_URL = "https://api.travelpayouts.com"

    MAX_RETRIES = 3
    INITIAL_DELAY = 2

    CACHE_EXPIRE = 3600


    def __init__(self):

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "X-Access-Token": settings.travelpayouts_api_key.get_secret_value(),
                "Accept-Encoding": "gzip",
            },
            timeout=httpx.Timeout(20.0),
        )


    async def close(
        self,
    ) -> None:

        await self.client.aclose()



    def _cache_key(
        self,
        origin: str,
        destination: str,
        departure_date: date,
    ) -> str:

        return (
            f"flight_price:"
            f"{origin}:"
            f"{destination}:"
            f"{departure_date.isoformat()}"
        )



    async def get_prices_for_dates(
        self,
        origin: str,
        destination: str,
        departure_date: date,
    ) -> PricesForDatesResponse:


        cache_key = self._cache_key(
            origin,
            destination,
            departure_date,
        )


        cached = await redis_cache.get(
            cache_key
        )


        if cached:

            logger.info(
                f"Redis cache hit: {cache_key}"
            )

            return PricesForDatesResponse.model_validate(
                json.loads(cached)
            )



        logger.info(
            f"Redis cache miss: {cache_key}"
        )


        delay = self.INITIAL_DELAY


        for attempt in range(
            1,
            self.MAX_RETRIES + 1,
        ):

            try:

                response = await self.client.get(
                    "/aviasales/v3/prices_for_dates",
                    params={
                        "origin": origin,
                        "destination": destination,
                        "departure_at": departure_date.isoformat(),
                        "currency": "rub",
                        "market": "ru",
                        "one_way": True,
                    },
                )


                if response.status_code == 429:

                    logger.warning(
                        f"TravelPayouts rate limit exceeded "
                        f"(attempt {attempt}/{self.MAX_RETRIES})"
                    )


                    if attempt < self.MAX_RETRIES:

                        await asyncio.sleep(
                            delay
                        )

                        delay *= 2

                        continue



                response.raise_for_status()


                data = PricesForDatesResponse.model_validate(
                    response.json()
                )


                await redis_cache.set(
                    cache_key,
                    data.model_dump_json(),
                    expire=self.CACHE_EXPIRE,
                )


                return data



            except (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.ReadError,
                httpx.RemoteProtocolError,
            ) as e:


                logger.warning(
                    f"TravelPayouts request failed "
                    f"(attempt {attempt}/{self.MAX_RETRIES}): {e}"
                )


                if attempt < self.MAX_RETRIES:

                    await asyncio.sleep(
                        delay
                    )

                    delay *= 2

                    continue


                raise



        raise RuntimeError(
            "TravelPayouts request failed after retries."
        )



    async def get_current_price(
        self,
        origin: str,
        destination: str,
        departure_date: date,
    ) -> int | None:


        response = await self.get_prices_for_dates(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
        )


        if not response.data:

            return None


        return response.data[0].price