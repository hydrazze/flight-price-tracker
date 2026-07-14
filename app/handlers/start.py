from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет! 👋\n\n"
        "Я Flight Price Tracker.\n"
        "Я помогу отслеживать стоимость авиабилетов."
    )