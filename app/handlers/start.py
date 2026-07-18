from aiogram import Router
from aiogram.types import Message

from app.keyboards.main import main_keyboard


router = Router()


@router.message(lambda message: message.text == "/start")
async def start_handler(message: Message):
    text = """
<b>✈️ Flight Price Tracker</b>

Отслеживаю цены на авиабилеты и присылаю уведомления, когда они падают.

<code>/track</code>   — начать отслеживание
<code>/tracks</code>  — мои отслеживания
<code>/archive</code> — история поездок
<code>/help</code>    — все возможности
"""
    await message.answer(text, reply_markup=main_keyboard)