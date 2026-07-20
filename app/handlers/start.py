from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.main import main_keyboard
from app.services.user import UserService

router = Router()


@router.message(lambda message: message.text == "/start")
async def start_handler(message: Message, session: AsyncSession):
    text = """
<b>✈️ Flight Price Tracker</b>

Отслеживаю цены на авиабилеты и присылаю уведомления, когда они падают.

/track   — начать отслеживание
/tracks  — мои отслеживания
/archive — история поездок
/help    — все возможности
"""

    await message.answer(text, reply_markup=main_keyboard)

    user_service = UserService(session)

    await user_service.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )