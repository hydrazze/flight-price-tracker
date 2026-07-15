from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.track import TrackRepository


class TrackService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.repository = TrackRepository(session)

    async def create_track(
        self,
        user_id: int,
        origin: str,
        destination: str,
        departure_date: date,
    ):
        return await self.repository.create(
            user_id=user_id,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
        )