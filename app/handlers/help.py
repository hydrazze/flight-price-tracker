from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message(lambda message: message.text == "/help")
async def help_handler(message: Message):
    text = """
<b>📋 Доступные команды</b>

<code>/track</code>   — ✈️ Создать отслеживание
<code>/tracks</code>  — 📡 Активные направления
<code>/archive</code> — 📦 Архив поездок
<code>/check</code>   — 🔍 Проверить цены сейчас

<i>По вопросам и предложениям: @hydraze</i>
"""
    await message.answer(text)