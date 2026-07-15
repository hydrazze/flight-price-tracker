from aiogram import Bot, Dispatcher

from app.config.settings import settings

from app.middlewares.database import DatabaseMiddleware


bot = Bot(token=settings.bot_token)

dispatcher = Dispatcher()

dispatcher.update.middleware(
    DatabaseMiddleware()
)