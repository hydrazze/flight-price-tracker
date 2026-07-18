import asyncio

from aiogram import Bot

from app.database.engine import async_session_maker
from app.repositories.track import TrackRepository
from app.providers.travelpayouts import TravelPayoutsClient
from app.services.price_checker import PriceCheckerService
from app.services.notification import NotificationService
from app.repositories.price_history import PriceHistoryRepository


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
            repository,
            client,
            notification_service,
            history_repository,
        )


        await service.check_prices()


        await client.close()



async def scheduler_loop(
    bot: Bot,
):

    while True:

        try:

            await run_price_checker(
                bot
            )


        except asyncio.CancelledError:
            raise


        except Exception as e:

            print(
                f"Scheduler error: {e}"
            )


        await asyncio.sleep(
            60
        )