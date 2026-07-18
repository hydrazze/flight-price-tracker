from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

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
        f"💰 Цель: "
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
            f"💰 Цель: "
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
            f"💰 Цель: "
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
        track_id
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