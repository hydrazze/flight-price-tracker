from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.services.user import UserService


router = Router()


@router.message(Command("start"))
async def start_handler(
    message: Message,
    session: AsyncSession,
) -> None:

    user_service = UserService(session)

    await user_service.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    await message.answer(
        "Привет! 👋\n\n"
        "Я Flight Price Tracker.\n"
        "Я помогу отслеживать стоимость авиабилетов."
    )