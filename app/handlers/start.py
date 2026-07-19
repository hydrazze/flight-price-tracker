from aiogram import Router
from aiogram.types import Message

from app.keyboards.main import main_keyboard


router = Router()


@router.message(lambda message: message.text == "/start")
async def start_handler(message: Message):
    text = """
<b>✈️ Flight Price Tracker</b>

Отслеживаю цены на авиабилеты и присылаю уведомления, когда они падают.

/track   — начать отслеживание
/tracks  — мои отслеживания
/archive — история поездок
/help    — все возможности
"""
    await message.answer(text, reply_markup=main_keyboard)