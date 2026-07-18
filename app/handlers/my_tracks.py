from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.fsm.context import FSMContext
from app.states.track import TrackState

from app.repositories.track import TrackRepository
from app.services.track import TrackService

from app.keyboards.tracks import (
    tracks_keyboard,
    track_detail_keyboard,
)

from app.keyboards.tracks import delete_confirm_keyboard

router = Router()


def get_track_status(track):

    if track.status.value == "available":
        return "✅ Рейсы найдены"

    elif track.status.value == "not_found":
        return "❌ Рейсы не найдены"

    elif track.status.value == "error":
        return "⚠️ Ошибка проверки"

    else:
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
        f"📅 Дата: {track.departure_date}\n"
        f"🎯 Цель: "
        f"{track.target_price or 'не указана'} ₽\n"
        f"📉 Сейчас: "
        f"{track.last_price or 'нет данных'} ₽\n"
        f"{get_track_status(track)}\n"
        f"🕒 Проверено: {last_checked}"
    )


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


    text = "Ваши отслеживания:\n\n"


    for track in tracks:

        text += (
            f"✈️ {track.origin} → {track.destination}\n"
            f"📅 {track.departure_date}\n"
            f"🎯 Цель: "
            f"{track.target_price or 'не указана'} ₽\n"
            f"📉 Сейчас: "
            f"{track.last_price or 'нет данных'} ₽\n\n"
        )


    await message.answer(
        text,
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
            "Трек не найден",
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



    text = "Ваши отслеживания:\n\n"


    for track in tracks:

        text += (
            f"✈️ {track.origin} → {track.destination}\n"
            f"📅 {track.departure_date}\n"
            f"🎯 Цель: "
            f"{track.target_price or 'не указана'} ₽\n"
            f"📉 Сейчас: "
            f"{track.last_price or 'нет данных'} ₽\n\n"
        )


    await callback.message.edit_text(
        text,
        reply_markup=tracks_keyboard(tracks),
    )


    await callback.answer()



# ==========================
# удалить трек
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


@router.message(
    TrackState.editing_target_price
)
async def process_new_target_price(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):

    data = await state.get_data()

    track_id = data["track_id"]


    if message.text == "-":

        target_price = None

    else:

        try:
            target_price = int(message.text)

        except ValueError:

            await message.answer(
                "❌ Введите число или '-'."
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


    if track.status.value == "available":

        status = "✅ Рейсы найдены"

    elif track.status.value == "not_found":

        status = "❌ Рейсы не найдены"

    elif track.status.value == "error":

        status = "⚠️ Ошибка проверки"

    else:

        status = "⏳ Ожидает проверки"


    text = (
        "✅ Целевая цена обновлена!\n\n"
        f"✈️ {track.origin} → {track.destination}\n\n"
        f"📅 Дата: {track.departure_date}\n"
        f"💰 Сейчас: {track.last_price or 'нет данных'} ₽\n"
        f"🎯 Цель: "
        f"{track.target_price if track.target_price is not None else 'не указана'} ₽"
        f"{status}\n"
    )


    if track.last_checked_at:

        text += (
            f"🕒 Проверено: "
            f"{track.last_checked_at.strftime('%d.%m.%Y %H:%M')}"
        )


    await message.answer(
        text,
        reply_markup=track_detail_keyboard(
            track.id
        ),
    )