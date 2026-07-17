import asyncio

from aiogram import Bot

from app.config.settings import settings
from app.database.engine import async_session_maker
from app.repositories.track import TrackRepository
from app.providers.travelpayouts import TravelPayoutsClient
from app.services.notification import NotificationService
from app.services.price_checker import PriceCheckerService
from app.repositories.price_history import PriceHistoryRepository


async def main():

    bot = Bot(
        token=settings.bot_token.get_secret_value()
    )

    async with async_session_maker() as session:

        repository = TrackRepository(
            session
        )

        history_repository = PriceHistoryRepository(session)

        client = TravelPayoutsClient()

        notification_service = NotificationService(
            bot
        )

        service = PriceCheckerService(
            repository,
            client,
            notification_service,
            history_repository           
        )

        await service.check_prices()

        await client.close()

    await bot.session.close()


asyncio.run(main())