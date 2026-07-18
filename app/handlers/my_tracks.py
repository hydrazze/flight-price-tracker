from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.track import TrackService
from app.database.engine import async_session_maker
from app.repositories.track import TrackRepository
from app.keyboards.tracks import tracks_keyboard


router = Router()


@router.message(Command(commands=["tracks"]))
async def my_tracks_handler(message: Message):

    async with async_session_maker() as session:

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

            if track.status.value == "available":
                status = "✅ Рейсы найдены"

            elif track.status.value == "not_found":
                status = "❌ Рейсы не найдены"

            elif track.status.value == "error":
                status = "⚠️ Ошибка проверки"

            else:
                status = "⏳ Ожидает проверки"


            last_checked = (
                track.last_checked_at.strftime("%d.%m.%Y %H:%M")
                if track.last_checked_at
                else "нет данных"
            )


            text += (
                f"✈️ {track.origin} → {track.destination}\n"
                f"📅 Дата: {track.departure_date}\n"
                f"💰 Цель: {track.target_price or 'не указана'} ₽\n"
                f"📉 Сейчас: {track.last_price or 'нет данных'} ₽\n"
                f"{status}\n"
                f"🕒 Проверено: {last_checked}\n\n"
            )


        await message.answer(
            text,
            reply_markup=tracks_keyboard(tracks),
        )


@router.callback_query(
    lambda c: c.data.startswith("delete_track:")
)
async def delete_track(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:

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
        await callback.answer(
            "Отслеживание не найдено.",
            show_alert=True,
        )

    await callback.answer()