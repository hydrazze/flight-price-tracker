"""Run one price check for all active tracks without starting polling."""
import asyncio

from app.bot import bot
from app.cache.redis import redis_cache
from app.database.engine import engine
from app.scheduler.checker import run_price_checker


async def main() -> None:
    try:
        await run_price_checker(bot)
    finally:
        await redis_cache.close()
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
