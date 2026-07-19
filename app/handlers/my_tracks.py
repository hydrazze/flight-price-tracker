from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.track import TrackRepository
from app.repositories.price_history import PriceHistoryRepository

from app.services.track import TrackService
from app.services.price_checker import PriceCheckerService
from app.services.notification import NotificationService

from app.providers.travelpayouts import TravelPayoutsClient

from app.keyboards.tracks import (
    tracks_keyboard,
    track_detail_keyboard,
    delete_confirm_keyboard,
    archive_keyboard,
)

from app.states.track import TrackState

from app.utils.track_formatter import (
    format_track,
    format_tracks_list,
    format_archive_track,
)

from app.bot import bot


router = Router()


# =====================================================
# /tracks
# =====================================================

@router.message(Command("tracks"))
async def my_tracks_handler(
    message: Message,
    session: AsyncSession,
):

    repository = TrackRepository(session)

    tracks = await repository.get_user_tracks(
        telegram_id=message.from_user.id
    )


    if not tracks:

        await message.answer(
            "📋 <b>Активных отслеживаний нет</b>\n\n"
            "Создайте первое отслеживание через кнопку ниже ✈️"
        )

        return


    await message.answer(
        format_tracks_list(tracks),
        reply_markup=tracks_keyboard(tracks),
    )



# =====================================================
# Открытие карточки трека
# =====================================================

@router.callback_query(
    lambda c: c.data.startswith("track:")
)
async def open_track(
    callback: CallbackQuery,
    session: AsyncSession,
):

    track_id = int(
        callback.data.split(":")[1]
    )


    repository = TrackRepository(session)


    track = await repository.get_by_id(
        track_id
    )


    if track is None:

        await callback.answer(
            "❌ Отслеживание не найдено.",
            show_alert=True,
        )

        return


    await callback.message.edit_text(
        format_track(track),
        reply_markup=track_detail_keyboard(
            track.id
        ),
    )


    await callback.answer()



# =====================================================
# Назад к списку
# =====================================================

@router.callback_query(
    lambda c: c.data == "back_to_tracks"
)
async def back_to_tracks(
    callback: CallbackQuery,
    session: AsyncSession,
):

    repository = TrackRepository(session)


    tracks = await repository.get_user_tracks(
        telegram_id=callback.from_user.id
    )


    if not tracks:

        await callback.message.edit_text(
            "📋 <b>Активных отслеживаний нет</b>"
        )

        await callback.answer()

        return



    await callback.message.edit_text(
        format_tracks_list(tracks),
        reply_markup=tracks_keyboard(tracks),
    )


    await callback.answer()



# =====================================================
# Удаление
# =====================================================

@router.callback_query(
    lambda c: c.data.startswith("delete_track:")
)
async def delete_track_confirm(
    callback: CallbackQuery,
):

    track_id = int(
        callback.data.split(":")[1]
    )


    await callback.message.edit_text(
        "🗑 <b>Удаление отслеживания</b>\n\n"
        "Вы уверены, что хотите удалить это направление?",
        reply_markup=delete_confirm_keyboard(
            track_id
        ),
    )


    await callback.answer()



@router.callback_query(
    lambda c: c.data.startswith("confirm_delete:")
)
async def confirm_delete(
    callback: CallbackQuery,
    session: AsyncSession,
):

    track_id = int(
        callback.data.split(":")[1]
    )


    service = TrackService(session)


    deleted = await service.delete_track(
        track_id,
        callback.from_user.id,
    )


    if deleted:

        await callback.message.edit_text(
            "✅ <b>Отслеживание удалено</b>\n\n"
            "Вернуться к списку можно через меню."
        )

    else:

        await callback.message.edit_text(
            "❌ Не удалось удалить отслеживание."
        )


    await callback.answer()



# =====================================================
# Изменение целевой цены
# =====================================================

@router.callback_query(
    lambda c: c.data.startswith("edit_target_price:")
)
async def edit_target_price(
    callback: CallbackQuery,
    state: FSMContext,
):

    track_id = int(
        callback.data.split(":")[1]
    )


    await state.update_data(
        track_id=track_id
    )


    await state.set_state(
        TrackState.editing_target_price
    )


    await callback.message.edit_text(
        "🎯 <b>Изменение целевой цены</b>\n\n"
        "Введите новую цену.\n\n"
        "Например:\n"
        "<code>12000</code>\n\n"
        "Чтобы убрать цель — отправьте <code>-</code>"
    )


    await callback.answer()



@router.message(
    TrackState.editing_target_price
)
async def process_edit_target_price(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):

    data = await state.get_data()


    track_id = data.get(
        "track_id"
    )


    target_price = None


    if message.text != "-":

        try:

            target_price = int(
                message.text
            )

        except ValueError:

            await message.answer(
                "❌ Введите число или отправьте '-'."
            )

            return



    service = TrackService(session)


    track = await service.update_target_price(
        track_id,
        target_price,
    )


    await state.clear()


    if track is None:

        await message.answer(
            "❌ Отслеживание не найдено."
        )

        return



    await message.answer(
        "✅ <b>Целевая цена обновлена</b>\n\n"
        + format_track(track),
        reply_markup=track_detail_keyboard(
            track.id
        ),
    )



# =====================================================
# История цены
# =====================================================

@router.callback_query(
    lambda c: c.data.startswith("price_history:")
)
async def show_price_history(
    callback: CallbackQuery,
    session: AsyncSession,
):

    track_id = int(
        callback.data.split(":")[1]
    )


    repository = PriceHistoryRepository(
        session
    )


    history = await repository.get_track_history(
        track_id
    )


    if not history:

        await callback.answer(
            "История цены пока пустая.",
            show_alert=True,
        )

        return



    text = (
        "📊 <b>История цены</b>\n\n"
    )


    for item in history[:10]:

        text += (
            f"💰 {item.price} ₽\n"
            f"🕒 {item.checked_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )


    await callback.message.edit_text(
        text,
        reply_markup=track_detail_keyboard(
            track_id
        ),
    )


    await callback.answer()



# =====================================================
# Проверка одного направления
# =====================================================

@router.callback_query(
    lambda c: c.data.startswith("check_track:")
)
async def check_track_now(
    callback: CallbackQuery,
    session: AsyncSession,
):

    track_id = int(
        callback.data.split(":")[1]
    )


    repository = TrackRepository(session)


    track = await repository.get_user_track(
        track_id=track_id,
        telegram_id=callback.from_user.id,
    )


    if track is None:

        await callback.answer(
            "❌ Отслеживание не найдено.",
            show_alert=True,
        )

        return



    client = TravelPayoutsClient()


    history_repository = PriceHistoryRepository(
        session
    )


    notification_service = NotificationService(
        bot
    )


    checker = PriceCheckerService(
        repository=repository,
        client=client,
        notification_service=notification_service,
        price_history_repository=history_repository,
    )


    await callback.answer(
        "🔄 Проверяю цену..."
    )


    await checker.check_one_track(
        track_id
    )


    track = await repository.get_by_id(
        track_id
    )


    await callback.message.edit_text(
        "✅ <b>Проверка завершена</b>\n\n"
        + format_track(track),
        reply_markup=track_detail_keyboard(
            track.id
        ),
    )



# =====================================================
# Архив
# =====================================================

@router.message(Command("archive"))
async def archive_handler(
    message: Message,
    session: AsyncSession,
):

    repository = TrackRepository(session)


    tracks = await repository.get_user_archive(
        telegram_id=message.from_user.id
    )


    if not tracks:

        await message.answer(
            "🗄 <b>Архив пуст</b>\n\n"
            "Здесь появятся завершенные поездки."
        )

        return



    text = (
        "🗄 <b>Архив поездок</b>\n\n"
    )


    for track in tracks:

        text += (
            format_archive_track(track)
            + "\n"
        )


    await message.answer(
        text,
        reply_markup=archive_keyboard(),
    )