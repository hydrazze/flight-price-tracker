from datetime import date

import httpx

from app.config.settings import settings
from app.schemas.travelpayouts import PricesForDatesResponse


class TravelPayoutsClient:

    BASE_URL = "https://api.travelpayouts.com"

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "X-Access-Token": settings.travelpayouts_api_key.get_secret_value(),
                "Accept-Encoding": "gzip",
            },
            timeout=20,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def get_prices_for_dates(
        self,
        origin: str,
        destination: str,
        departure_date: date,
    ) -> PricesForDatesResponse:

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

        response.raise_for_status()

        return PricesForDatesResponse.model_validate(
            response.json()
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