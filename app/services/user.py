from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository
from app.models import User


class UserService:

    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
    ) -> User:

        user = await self.repository.get_by_telegram_id(
            telegram_id
        )

        if user:
            return user

        return await self.repository.create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )