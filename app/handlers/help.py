from aiogram import Router, F
from aiogram.types import Message, CallbackQuery


router = Router()


HELP_TEXT = """
<b>📋 Доступные команды</b>

✈️ /track — создать отслеживание

📡 /tracks — мои отслеживания

📦 /archive — архив поездок

🔍 /check — проверить цены сейчас

<i>По вопросам и предложениям:</i> @hydraze
"""


def help_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="main_menu",
                )
            ]
        ]
    )


@router.message(F.text == "/help")
async def help_handler(
    message: Message,
):

    await message.answer(
        HELP_TEXT,
        reply_markup=help_keyboard(),
    )


@router.callback_query(
    F.data == "help"
)
async def help_callback(
    callback: CallbackQuery,
):

    await callback.message.edit_text(
        HELP_TEXT,
        reply_markup=help_keyboard(),
    )

    await callback.answer()