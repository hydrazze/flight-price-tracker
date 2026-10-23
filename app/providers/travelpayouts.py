import asyncio
from datetime import date

import httpx
from pydantic import ValidationError

from app.cache.redis import redis_cache
from app.config.settings import settings
from app.logging.logger import logger
from app.models.enums import StopPreference
from app.schemas.travelpayouts import FlightPrice, PricesForDatesResponse


class TravelPayoutsClient:
    BASE_URL = "https://api.travelpayouts.com"
    MAX_RETRIES = 3
    INITIAL_DELAY = 2
    CACHE_EXPIRE = 3600
    PAGE_SIZE = 1000

    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "X-Access-Token": settings.travelpayouts_api_key.get_secret_value(),
                "Accept-Encoding": "gzip",
            },
            timeout=httpx.Timeout(20.0),
        )

    async def close(self) -> None:
        await self.client.aclose()

    def _cache_key(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
        stop_preference: StopPreference = StopPreference.ANY,
    ) -> str:
        # A new namespace prevents reuse of legacy one-way responses.
        return (
            f"flight_price:v2:{origin}:{destination}:{departure_date.isoformat()}:"
            f"{return_date.isoformat() if return_date else 'one_way'}:"
            f"{StopPreference(stop_preference).value}"
        )

    @staticmethod
    def _matches(
        flight: FlightPrice,
        departure_date: date,
        return_date: date | None,
        stop_preference: StopPreference,
    ) -> bool:
        if flight.departure_at.date() != departure_date:
            return False
        if return_date is None:
            if flight.return_at is not None:
                return False
        elif flight.return_at is None or flight.return_at.date() != return_date:
            return False

        if stop_preference == StopPreference.DIRECT:
            return flight.transfers == 0 and (
                return_date is None or flight.return_transfers == 0
            )
        if stop_preference == StopPreference.WITH_STOPS:
            # A connection on either leg makes a round trip a connecting itinerary.
            return flight.transfers > 0 or (
                return_date is not None
                and flight.return_transfers is not None
                and flight.return_transfers > 0
            )
        return True

    async def _get_page(self, params: dict) -> PricesForDatesResponse:
        delay = self.INITIAL_DELAY
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = await self.client.get(
                    "/aviasales/v3/prices_for_dates", params=params,
                )
                if response.status_code == 429 and attempt < self.MAX_RETRIES:
                    logger.warning("Travelpayouts rate limit; retrying request")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                response.raise_for_status()
                data = PricesForDatesResponse.model_validate(response.json())
                if not data.success:
                    raise RuntimeError("Travelpayouts returned an unsuccessful response")
                return data
            except (
                httpx.TimeoutException, httpx.ConnectError,
                httpx.ReadError, httpx.RemoteProtocolError,
            ):
                if attempt == self.MAX_RETRIES:
                    raise
                logger.warning("Travelpayouts connection failed; retrying request")
                await asyncio.sleep(delay)
                delay *= 2
        raise RuntimeError("Travelpayouts request failed after retries")

    async def get_prices_for_dates(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
        stop_preference: StopPreference = StopPreference.ANY,
    ) -> PricesForDatesResponse:
        stop_preference = StopPreference(stop_preference)
        if return_date is not None and return_date < departure_date:
            raise ValueError("Return date cannot precede departure date")
        cache_key = self._cache_key(
            origin, destination, departure_date, return_date, stop_preference,
        )
        cached = await redis_cache.get(cache_key)
        if cached:
            try:
                data = PricesForDatesResponse.model_validate_json(cached)
                if not data.success:
                    raise ValueError("Unsuccessful cached response")
            except (ValidationError, ValueError):
                logger.warning("Invalid cached price response; fetching from provider")
                await redis_cache.delete(cache_key)
            else:
                logger.info(f"Redis cache hit: {cache_key}")
                return data

        params = {
            "origin": origin,
            "destination": destination,
            "departure_at": departure_date.isoformat(),
            "one_way": return_date is None,
            "direct": stop_preference == StopPreference.DIRECT,
            "currency": "rub",
            "market": "ru",
            "sorting": "price",
            "unique": False,
            "limit": self.PAGE_SIZE,
            "page": 1,
        }
        if return_date is not None:
            params["return_at"] = return_date.isoformat()

        flights = []
        previous_page = None
        while True:
            data = await self._get_page(params)
            # Do not silently report no flights if the provider ignores pagination.
            if len(data.data) == self.PAGE_SIZE:
                current_page = data.model_dump_json()
                if current_page == previous_page:
                    raise RuntimeError("Travelpayouts repeated a page of results")
                previous_page = current_page
            flights.extend(
                flight for flight in data.data
                if self._matches(flight, departure_date, return_date, stop_preference)
            )
            if len(data.data) < self.PAGE_SIZE:
                break
            params["page"] += 1

        result = PricesForDatesResponse(success=True, data=flights, currency=data.currency)
        await redis_cache.set(cache_key, result.model_dump_json(), expire=self.CACHE_EXPIRE)
        return result

    async def get_current_price(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
        stop_preference: StopPreference = StopPreference.ANY,
    ) -> int | None:
        response = await self.get_prices_for_dates(
            origin, destination, departure_date, return_date, stop_preference,
        )
        return min((flight.price for flight in response.data), default=None)
