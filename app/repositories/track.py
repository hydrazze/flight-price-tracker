from datetime import date

from sqlalchemy import select
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
        target_price: int | None = None,
    ) -> Track:

        track = Track(
            user_id=user_id,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            target_price=target_price,
        )

        self.session.add(track)

        await self.session.commit()

        await self.session.refresh(track)

        return track

    async def get_active_tracks(
        self,
    ) -> list[Track]:

        result = await self.session.execute(
            select(Track).where(
                Track.active.is_(True)
            )
        )

        return list(result.scalars().all())

    async def save(
        self,
        track: Track,
    ) -> None:

        await self.session.commit()

    async def update_last_price(
        self,
        track: Track,
        price: int,
    ) -> None:

        track.last_price = price

        await self.session.commit()