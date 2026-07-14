from aiogram import Bot, Dispatcher

from app.config.settings import settings


bot = Bot(token=settings.bot_token)

dispatcher = Dispatcher()