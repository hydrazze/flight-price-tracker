import asyncio

from app.bot import bot, dispatcher
from app.handlers import router
from app.scheduler.checker import run_price_checker
from app.scheduler.checker import scheduler_loop

async def main() -> None:

    dispatcher.include_router(router)

    asyncio.create_task(
        scheduler_loop()
    )

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())