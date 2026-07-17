import asyncio

from app.database.engine import async_session_maker
from app.repositories.track import TrackRepository
from app.providers.travelpayouts import TravelPayoutsClient
from app.services.price_checker import PriceCheckerService
from app.services.notification import NotificationService
from app.repositories.price_history import PriceHistoryRepository

from aiogram import Bot

from app.config.settings import settings


async def run_price_checker():

    async with async_session_maker() as session:

        repository = TrackRepository(session)

        history_repository = PriceHistoryRepository(session)

        client = TravelPayoutsClient()

        bot = Bot(
            token=settings.bot_token.get_secret_value()
        )

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
    
async def scheduler_loop():

    while True:

        try:
            await run_price_checker()

        except Exception as e:
            print(
                f"Scheduler error: {e}"
            )

        await asyncio.sleep(
            60
        )