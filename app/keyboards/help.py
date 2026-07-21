from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


help_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🏠 Главное меню",
                callback_data="main_menu",
            )
        ]
    ]
)
