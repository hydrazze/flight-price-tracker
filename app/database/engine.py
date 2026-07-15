from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=True,
)


async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)