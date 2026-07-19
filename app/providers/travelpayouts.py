from datetime import date
import asyncio

import httpx

from app.config.settings import settings
from app.schemas.travelpayouts import PricesForDatesResponse

from app.logging.logger import logger


class TravelPayoutsClient:

    BASE_URL = "https://api.travelpayouts.com"


    def __init__(self):

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "X-Access-Token": settings.travelpayouts_api_key.get_secret_value(),
                "Accept-Encoding": "gzip",
            },
            timeout=httpx.Timeout(
                20.0
            ),
        )


    async def close(self) -> None:

        await self.client.aclose()



    async def get_prices_for_dates(
        self,
        origin: str,
        destination: str,
        departure_date: date,
    ) -> PricesForDatesResponse:

        retries = 3


        for attempt in range(
            1,
            retries + 1,
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
                        "TravelPayouts rate limit exceeded. "
                        f"Attempt {attempt}/{retries}"
                    )

                    if attempt < retries:

                        await asyncio.sleep(
                            5
                        )

                        continue



                response.raise_for_status()


                return PricesForDatesResponse.model_validate(
                    response.json()
                )


            except (
                httpx.TimeoutException,
                httpx.ConnectError,
            ) as e:


                logger.warning(
                    f"TravelPayouts connection error "
                    f"attempt {attempt}/{retries}: {e}"
                )


                if attempt < retries:

                    await asyncio.sleep(
                        5
                    )

                    continue


                raise



        raise RuntimeError(
            "TravelPayouts request failed after retries"
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