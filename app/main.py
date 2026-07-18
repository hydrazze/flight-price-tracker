import asyncio

from app.bot import bot, dispatcher
from app.handlers import router, check, help
from app.scheduler.checker import scheduler_loop
from app.commands import set_bot_commands


scheduler_task: asyncio.Task | None = None


async def start_scheduler() -> None:
    global scheduler_task

    scheduler_task = asyncio.create_task(
        scheduler_loop(bot)
    )


async def stop_scheduler() -> None:
    global scheduler_task

    if scheduler_task is not None:

        scheduler_task.cancel()

        try:
            await scheduler_task

        except asyncio.CancelledError:
            pass


async def main() -> None:

    dispatcher.include_router(router)
    dispatcher.include_router(check.router)
    dispatcher.include_router(help.router)

    await set_bot_commands(
        bot
    )

    asyncio.create_task(
        scheduler_loop(
            bot
        )
    )

    await dispatcher.start_polling(
        bot,
        close_bot_session=True,
    )


if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("Bot stopped")

    except asyncio.CancelledError:
        pass