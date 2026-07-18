from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database.engine import async_session_maker
from app.repositories.track import TrackRepository
from app.repositories.price_history import PriceHistoryRepository
from app.providers.travelpayouts import TravelPayoutsClient
from app.services.price_checker import PriceCheckerService
from app.services.notification import NotificationService

from aiogram import Bot

from app.config.settings import settings


router = Router()


@router.message(Command("check"))
async def check_handler(
    message: Message,
    bot: Bot,
):

    await message.answer(
        "🔎 Проверяю цены..."
    )


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


        await service.check_prices()


        await client.close()


    await message.answer(
        "✅ Проверка завершена."
    )
