import asyncio

from app.bot import bot, dispatcher
from app.handlers import router, check, help
from app.scheduler.checker import scheduler_loop
from app.commands import set_bot_commands

from app.database.engine import engine
from app.logging.logger import logger


scheduler_task: asyncio.Task | None = None



async def start_scheduler() -> None:

    global scheduler_task

    scheduler_task = asyncio.create_task(
        scheduler_loop(bot)
    )

    logger.info(
        "Scheduler task created"
    )



async def stop_scheduler() -> None:

    global scheduler_task

    if scheduler_task is not None:

        logger.info(
            "Stopping scheduler..."
        )

        scheduler_task.cancel()

        try:

            await scheduler_task

        except asyncio.CancelledError:

            pass



async def shutdown() -> None:

    logger.info(
        "Application shutdown started"
    )


    await stop_scheduler()


    await bot.session.close()


    await engine.dispose()


    logger.info(
        "Application shutdown completed"
    )



async def main() -> None:

    dispatcher.include_router(
        router
    )

    dispatcher.include_router(
        check.router
    )

    dispatcher.include_router(
        help.router
    )


    await set_bot_commands(
        bot
    )


    await start_scheduler()


    logger.info(
        "Bot started"
    )


    try:

        await dispatcher.start_polling(
            bot,
            close_bot_session=False,
        )


    finally:

        await shutdown()



if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "Bot stopped manually"
        )