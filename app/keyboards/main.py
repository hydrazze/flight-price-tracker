from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[

        [
            InlineKeyboardButton(
                text="✈️ Создать отслеживание",
                callback_data="create_track",
            )
        ],

        [
            InlineKeyboardButton(
                text="📋 Мои отслеживания",
                callback_data="my_tracks",
            ),

            InlineKeyboardButton(
                text="🗄 Архив",
                callback_data="archive",
            )
        ],

        [
            InlineKeyboardButton(
                text="🔄 Проверить цены",
                callback_data="check_prices",
            )
        ],

        [
            InlineKeyboardButton(
                text="❓ Помощь",
                callback_data="help",
            )
        ],

    ]
)



def main_menu_keyboard():

    return main_keyboard