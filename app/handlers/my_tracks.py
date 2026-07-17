from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import CallbackQuery

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

            text += (
                f"✈️ {track.origin} → {track.destination}\n"
                f"📅 {track.departure_date}\n"
                f"💰 Цель: {track.target_price or 'не указана'} ₽\n"
                f"📉 Сейчас: {track.last_price or 'нет данных'} ₽\n\n"
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