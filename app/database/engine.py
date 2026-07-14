from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config.settings import settings


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=True,
)