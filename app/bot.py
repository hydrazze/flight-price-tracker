from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config.settings import settings
from app.middlewares.database import DatabaseMiddleware


bot = Bot(
    token=settings.bot_token.get_secret_value(),
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dispatcher = Dispatcher()

dispatcher.update.middleware(
    DatabaseMiddleware()
)
