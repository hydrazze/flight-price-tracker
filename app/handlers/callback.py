from aiogram import Router, F
from aiogram.types import CallbackQuery

from aiogram.fsm.context import FSMContext

from app.states.track import TrackState
from app.utils.track_formatter import format_tracks_list, format_archive_track

from app.keyboards.main import main_keyboard
from app.keyboards.tracks import (
    archive_keyboard,
    tracks_keyboard,
)
from app.handlers.help import HELP_TEXT, help_keyboard

from app.database.engine import async_session_maker

from app.repositories.track import TrackRepository
from app.repositories.price_history import PriceHistoryRepository

from app.providers.travelpayouts import TravelPayoutsClient

from app.services.price_checker import PriceCheckerService
from app.services.notification import NotificationService

from app.bot import bot


router = Router()



@router.callback_query(
    F.data == "cancel_track"
)
async def cancel_track(
    callback: CallbackQuery,
    state: FSMContext,
):

    await state.clear()


    await callback.message.answer(
        "❌ Создание отслеживания отменено.",
        reply_markup=main_keyboard,
    )


    await callback.answer()



@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "✈️ <b>Flight Price Tracker</b>\n\n"
        "Отслеживаю цены на авиабилеты и присылаю уведомления, когда они падают.\n\n"
        "/track   — начать отслеживание\n"
        "/tracks  — мои отслеживания\n"
        "/archive — история поездок\n"
        "/help    — все возможности",
        reply_markup=main_keyboard,
    )

    await callback.answer()



@router.callback_query(
    F.data == "my_tracks"
)
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
                "📋 У вас пока нет активных отслеживаний.",
                reply_markup=main_keyboard,
            )

            await callback.answer()
            return



        await callback.message.answer(
            format_tracks_list(tracks),
            reply_markup=tracks_keyboard(tracks),
        )


    await callback.answer()



@router.callback_query(
    F.data == "archive"
)
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
                "🗄 Архив пуст.",
                reply_markup=main_keyboard,
            )

            await callback.answer()
            return



        text = "🗄 <b>Архив поездок</b>\n\n" + "\n\n".join(
            format_archive_track(track) for track in tracks
        )

        await callback.message.answer(
            text,
            reply_markup=archive_keyboard(),
        )

    await callback.answer()



@router.callback_query(
    F.data == "check_prices"
)
async def check_prices_callback(
    callback: CallbackQuery,
):

    await callback.message.answer(
        "🔄 Проверяю цены..."
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



    async with async_session_maker() as session:

        repository = TrackRepository(session)

        tracks = await repository.get_user_tracks(
            telegram_id=callback.from_user.id
        )


    if tracks:

        await callback.message.answer(
            format_tracks_list(tracks),
            reply_markup=tracks_keyboard(tracks),
        )

    else:

        await callback.message.answer(
            "📋 Активных отслеживаний нет.",
            reply_markup=main_keyboard,
        )

    await callback.answer()



@router.callback_query(
    F.data == "help"
)
async def help_callback(
    callback: CallbackQuery,
):

    await callback.message.answer(
        HELP_TEXT,
        reply_markup=help_keyboard(),
    )

    await callback.answer()