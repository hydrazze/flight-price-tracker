import asyncio

from aiogram import Bot

from app.database.engine import async_session_maker
from app.repositories.track import TrackRepository
from app.providers.travelpayouts import TravelPayoutsClient
from app.services.price_checker import PriceCheckerService
from app.services.notification import NotificationService
from app.repositories.price_history import PriceHistoryRepository

from app.config.settings import settings
from app.logging.logger import logger



async def run_price_checker(
    bot: Bot,
):

    async with async_session_maker() as session:

        repository = TrackRepository(
            session
        )


        history_repository = PriceHistoryRepository(
            session
        )


        client = TravelPayoutsClient()


        notification_service = NotificationService(
            bot
        )


        service = PriceCheckerService(
            repository=repository,
            client=client,
            notification_service=notification_service,
            price_history_repository=history_repository,
        )


        try:

            await service.check_prices()


        finally:

            await client.close()



async def scheduler_loop(
    bot: Bot,
):

    logger.info(
        "Scheduler started"
    )


    while True:

        try:

            await run_price_checker(
                bot
            )


        except asyncio.CancelledError:

            logger.info(
                "Scheduler stopped"
            )

            raise


        except Exception:

            logger.exception(
                "Scheduler error"
            )


        await asyncio.sleep(
            settings.price_check_interval
        )