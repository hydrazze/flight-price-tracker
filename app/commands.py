from aiogram import Bot
from aiogram.types import BotCommand


async def set_bot_commands(
    bot: Bot,
):

    commands = [

        BotCommand(
            command="start",
            description="🚀 Главное меню",
        ),

        BotCommand(
            command="track",
            description="✈️ Новое отслеживание",
        ),

        BotCommand(
            command="tracks",
            description="📋 Мои отслеживания",
        ),

        BotCommand(
            command="archive",
            description="🗄 Архив",
        ),

        BotCommand(
            command="check",
            description="🔄 Проверить цены",
        ),

        BotCommand(
            command="help",
            description="❓ Помощь",
        ),
    ]


    await bot.set_my_commands(
        commands
    )