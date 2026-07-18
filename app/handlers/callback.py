from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.database.engine import async_session_maker
from app.repositories.track import TrackRepository
from app.repositories.price_history import PriceHistoryRepository
from app.providers.travelpayouts import TravelPayoutsClient
from app.services.price_checker import PriceCheckerService
from app.services.notification import NotificationService

from app.bot import bot


router = Router()


@router.callback_query(F.data == "create_track")
async def create_track_callback(
    callback: CallbackQuery,
):
    await callback.message.answer(
        "✈️ Создание нового отслеживания\n\n"
        "Введите город отправления:"
    )

    await callback.answer()



@router.callback_query(F.data == "my_tracks")
async def my_tracks_callback(
    callback: CallbackQuery,
):

    async with async_session_maker() as session:

        repository = TrackRepository(
            session
        )

        tracks = await repository.get_user_tracks(
            telegram_id=callback.from_user.id
        )


        if not tracks:

            await callback.message.answer(
                "📋 У вас нет активных отслеживаний."
            )

            await callback.answer()
            return


        text = "📋 Ваши активные отслеживания:\n\n"


        for track in tracks:

            text += (
                f"✈️ {track.origin} → {track.destination}\n"
                f"📅 {track.departure_date.strftime('%d.%m.%Y')}\n"
                f"💰 {track.last_price if track.last_price else 'нет данных'} ₽\n\n"
            )


        await callback.message.answer(
            text
        )


    await callback.answer()



@router.callback_query(F.data == "archive")
async def archive_callback(
    callback: CallbackQuery,
):

    async with async_session_maker() as session:

        repository = TrackRepository(
            session
        )


        tracks = await repository.get_user_archive(
            telegram_id=callback.from_user.id
        )


        if not tracks:

            await callback.message.answer(
                "🗄 Архив пуст."
            )

            await callback.answer()
            return



        text = "🗄 Архив поездок:\n\n"


        for track in tracks:

            text += (
                f"✈️ {track.origin} → {track.destination}\n"
                f"📅 {track.departure_date.strftime('%d.%m.%Y')}\n\n"
            )


        await callback.message.answer(
            text
        )


    await callback.answer()



@router.callback_query(F.data == "check_prices")
async def check_prices_callback(
    callback: CallbackQuery,
):

    await callback.message.answer(
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



    await callback.message.answer(
        "✅ Проверка завершена."
    )


    await callback.answer()



@router.callback_query(F.data == "help")
async def help_callback(
    callback: CallbackQuery,
):

    await callback.message.answer(
        """
📋 Доступные команды

✈️ /track — создать отслеживание

📡 /tracks — активные направления

📦 /archive — архив поездок

🔍 /check — проверить цены сейчас

<i>По вопросам и предложениям: @hydraze</i>
"""
    )


    await callback.answer()