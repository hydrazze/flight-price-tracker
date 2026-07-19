from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


cancel_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel_track",
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu",
            )
        ],
    ]
)