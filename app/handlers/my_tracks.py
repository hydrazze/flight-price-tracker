from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession


from app.states.track import TrackState


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
)


from app.bot import bot


router = Router()



def get_track_status(track):

    if track.status.value == "available":
        return "✅ Рейсы найдены"

    elif track.status.value == "not_found":
        return "❌ Рейсы не найдены"

    elif track.status.value == "error":
        return "⚠️ Ошибка проверки"

    return "⏳ Ожидает проверки"



def format_track(track):

    last_checked = (
        track.last_checked_at.strftime(
            "%d.%m.%Y %H:%M"
        )
        if track.last_checked_at
        else "нет данных"
    )


    return (
        f"✈️ {track.origin} → {track.destination}\n\n"
        f"📅 Дата: {track.departure_date.strftime('%d-%m-%Y')}\n"
        f"🎯 Цель: "
        f"{track.target_price if track.target_price is not None else 'не указана'} ₽\n"
        f"📉 Сейчас: "
        f"{track.last_price if track.last_price is not None else 'нет данных'} ₽\n"
        f"{get_track_status(track)}\n"
        f"🕒 Проверено: {last_checked}"
    )



def format_tracks_list(tracks):

    text = "Ваши отслеживания:\n\n"


    for track in tracks:

        text += (
            f"✈️ {track.origin} → {track.destination}\n"
            f"📅 {track.departure_date.strftime('%d-%m-%Y')}\n"
            f"🎯 Цель: "
            f"{track.target_price if track.target_price is not None else 'не указана'} ₽\n"
            f"📉 Сейчас: "
            f"{track.last_price if track.last_price is not None else 'нет данных'} ₽\n\n"
        )


    return text



# ==========================
# /tracks
# ==========================

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
            "У вас нет активных отслеживаний."
        )

        return


    await message.answer(
        format_tracks_list(tracks),
        reply_markup=tracks_keyboard(tracks),
    )
# ==========================
# открыть конкретный трек
# ==========================

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
            "❌ Трек не найден.",
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



# ==========================
# назад к списку
# ==========================

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
            "У вас нет активных отслеживаний."
        )

        await callback.answer()

        return


    await callback.message.edit_text(
        format_tracks_list(tracks),
        reply_markup=tracks_keyboard(tracks),
    )


    await callback.answer()



# ==========================
# удаление трека
# ==========================

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
        "❗ Вы уверены, что хотите удалить это отслеживание?",
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
            "✅ Отслеживание удалено."
        )

    else:

        await callback.message.edit_text(
            "❌ Не удалось удалить отслеживание."
        )


    await callback.answer()



# ==========================
# изменение целевой цены
# ==========================

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
        "Введите новую целевую цену.\n\n"
        "Например:\n"
        "7000\n\n"
        "Или отправьте '-' чтобы убрать целевую цену."
    )


    await callback.answer()



@router.message(TrackState.waiting_target_price)
async def process_target_price(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:

    data = await state.get_data()

    target_price: int | None = None


    if message.text != "-":

        try:
            target_price = int(message.text)

        except ValueError:

            await message.answer(
                "❌ Цена должна быть числом.\n\n"
                "Например: 15000\n"
                "Или отправьте '-' чтобы отслеживать любые изменения."
            )

            return


        if target_price <= 0:

            await message.answer(
                "❌ Цена должна быть больше 0 ₽."
            )

            return


        if target_price > 1_000_000:

            await message.answer(
                "❌ Слишком большая цена.\n"
                "Введите сумму до 1 000 000 ₽."
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
        "✅ Целевая цена обновлена!\n\n"
        + format_track(track),
        reply_markup=track_detail_keyboard(
            track.id
        ),
    )



# ==========================
# история цены
# ==========================

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



    text = "📊 История цены\n\n"


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



# ==========================
# ручная проверка цены
# ==========================

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
        "✅ Проверка завершена!\n\n"
        + format_track(track),
        reply_markup=track_detail_keyboard(
            track.id
        ),
    )