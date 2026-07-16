from app.providers.travelpayouts import TravelPayoutsClient
from app.database.session import AsyncSessionLocal
from app.repositories.track import TrackRepository
from app.services.price_checker import PriceCheckerService


async def run_price_checker():

    async with AsyncSessionLocal() as session:

        repository = TrackRepository(session)

        client = TravelPayoutsClient()

        service = PriceCheckerService(
            repository=repository,
            client=client,
        )

        await service.check_prices()

        await client.close()