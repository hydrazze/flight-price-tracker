from aiogram import Bot, Dispatcher

from app.config.settings import settings

from app.middlewares.database import DatabaseMiddleware


bot = Bot(token=settings.bot_token.get_secret_value())

dispatcher = Dispatcher()

dispatcher.update.middleware(
    DatabaseMiddleware()
)
