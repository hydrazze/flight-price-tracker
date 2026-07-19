from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.keyboards.main import main_keyboard


router = Router()


HELP_TEXT = """
<b>📋 Доступные команды</b>

/track   — ✈️ Создать отслеживание
/tracks  — 📡 Активные направления
/archive — 📦 Архив поездок
/check   — 🔍 Проверить цены сейчас

<i>По вопросам и предложениям:</i> @hydraze
"""


@router.message(F.text == "/help")
async def help_handler(
    message: Message,
):

    await message.answer(
        HELP_TEXT,
        reply_markup=main_keyboard,
    )


@router.callback_query(
    F.data == "help"
)
async def help_callback(
    callback: CallbackQuery,
):

    await callback.message.edit_text(
        HELP_TEXT,
        reply_markup=main_keyboard,
    )

    await callback.answer()