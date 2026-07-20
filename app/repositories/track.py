from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import TrackStatus
from app.models.track import Track
from app.models.user import User


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
            select(Track)
            .options(
                selectinload(Track.user)
            )
            .where(
                Track.active.is_(True)
            )
        )

        return list(
            result.scalars().all()
        )


    async def get_user_tracks(
        self,
        telegram_id: int,
    ) -> list[Track]:

        result = await self.session.execute(
            select(Track)
            .join(User)
            .where(
                User.telegram_id == telegram_id,
                Track.active.is_(True),
            )
        )

        return list(
            result.scalars().all()
        )


    async def get_user_archive(
        self,
        telegram_id: int,
    ) -> list[Track]:

        result = await self.session.execute(
            select(Track)
            .join(User)
            .where(
                User.telegram_id == telegram_id,
                Track.status == TrackStatus.ARCHIVED,
            )
            .order_by(
                Track.departure_date.desc()
            )
        )

        return list(
            result.scalars().all()
        )


    async def get_by_id(
        self,
        track_id: int,
    ) -> Track | None:

        result = await self.session.execute(
            select(Track)
            .where(
                Track.id == track_id
            )
        )

        return result.scalar_one_or_none()


    async def get_user_track(
        self,
        track_id: int,
        telegram_id: int,
    ) -> Track | None:

        result = await self.session.execute(
            select(Track)
            .join(User)
            .where(
                Track.id == track_id,
                User.telegram_id == telegram_id,
                Track.active.is_(True),
            )
        )

        return result.scalar_one_or_none()


    async def update_target_price(
        self,
        track: Track,
        target_price: int | None,
    ) -> Track:

        track.target_price = target_price

        await self.session.commit()
        await self.session.refresh(track)

        return track

    async def delete(self, track: Track) -> None:
        await self.session.delete(track)
        await self.session.commit()

    async def exists(
        self,
        user_id: int,
        origin: str,
        destination: str,
        departure_date: date,
    ) -> bool:

        result = await self.session.execute(
            select(Track)
            .where(
                Track.user_id == user_id,
                Track.origin == origin,
                Track.destination == destination,
                Track.departure_date == departure_date,
                Track.active.is_(True),
            )
        )

        return result.scalar_one_or_none() is not None


    async def archive_expired_tracks(
        self,
        today: date,
    ) -> list[Track]:

        result = await self.session.execute(
            select(Track)
            .options(
                selectinload(Track.user)
            )
            .where(
                Track.active.is_(True),
                Track.departure_date < today,
            )
        )

        tracks = list(
            result.scalars().all()
        )

        for track in tracks:

            track.active = False
            track.status = TrackStatus.ARCHIVED


        await self.session.commit()

        return tracks


    async def save(
        self,
    ) -> None:

        await self.session.commit()


    async def save_all(
        self,
        tracks: list[Track],
    ) -> None:

        self.session.add_all(tracks)

        await self.session.commit()