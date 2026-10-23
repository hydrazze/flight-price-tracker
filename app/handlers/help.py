from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from app.keyboards.help import help_keyboard


router = Router()


HELP_TEXT = """
<b>📋 Доступные команды</b>

✈️ /track — создать отслеживание\nВ одну сторону или туда и обратно; выбор пересадок.

📡 /tracks — мои отслеживания

📦 /archive — архив поездок

🔍 /check — проверить цены сейчас

<i>По вопросам и предложениям:</i> @hydraze
"""


@router.message(Command("help"))
async def help_handler(
    message: Message,
):

    await message.answer(
        HELP_TEXT,
        reply_markup=help_keyboard,
    )


@router.callback_query(
    F.data == "help"
)
async def help_callback(
    callback: CallbackQuery,
):

    await callback.message.edit_text(
        HELP_TEXT,
        reply_markup=help_keyboard,
    )

    await callback.answer()