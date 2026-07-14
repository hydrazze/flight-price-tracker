import asyncio

from app.bot import bot, dispatcher
from app.handlers import router


async def main() -> None:
    dispatcher.include_router(router)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())