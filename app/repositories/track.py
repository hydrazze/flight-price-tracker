from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.track import Track


class TrackRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        user_id: int,
        origin: str,
        destination: str,
        departure_date: date,
    ) -> Track:

        track = Track(
            user_id=user_id,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
        )

        self.session.add(track)

        await self.session.commit()

        await self.session.refresh(track)

        return track