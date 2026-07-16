import asyncio

from app.database.engine import async_session_maker
from app.repositories.track import TrackRepository
from app.providers.travelpayouts import TravelPayoutsClient
from app.services.price_checker import PriceCheckerService


async def main():

    async with async_session_maker() as session:

        repository = TrackRepository(
            session
        )

        client = TravelPayoutsClient()

        service = PriceCheckerService(
            repository,
            client,
        )

        await service.check_prices()

        await client.close()


asyncio.run(main())