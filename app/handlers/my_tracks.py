from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import async_session_maker
from app.repositories.track import TrackRepository


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


        await message.answer(text)