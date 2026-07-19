from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.track import TrackRepository


class TrackService:
    def __init__(self, session: AsyncSession):
        self.repository = TrackRepository(session)

    def _normalize_airport(self, value: str | dict | None) -> str:
        if isinstance(value, dict):
            code = value.get("code")
            if code:
                return str(code).strip().upper()
            return str(value.get("city", "")).strip()

        if value is None:
            return ""

        return str(value).strip()

    async def create_track(
        self,
        user_id: int,
        origin: str | dict,
        destination: str | dict,
        departure_date: date,
        target_price: int | None = None,
    ):
        origin = self._normalize_airport(origin)
        destination = self._normalize_airport(destination)

        exists = await self.repository.exists(
            user_id=user_id,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
        )

        if exists:
            return None

        return await self.repository.create(
            user_id=user_id,
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            target_price=target_price,
        )

    async def delete_track(
        self,
        track_id: int,
        telegram_id: int,
    ) -> bool:

        track = await self.repository.get_user_track(
            track_id,
            telegram_id,
        )


        if track is None:

            return False


        await self.repository.delete(
            track
        )


        return True



    async def update_target_price(
        self,
        track_id: int,
        target_price: int | None,
    ):

        track = await self.repository.get_by_id(
            track_id
        )


        if track is None:

            return None


        return await self.repository.update_target_price(
            track,
            target_price,
        )