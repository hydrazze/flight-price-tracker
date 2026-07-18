from app.models.price_history import PriceHistory

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select


class PriceHistoryRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session


    async def get_track_history(
        self,
        track_id: int,
    ):
        result = await self.session.execute(
            select(PriceHistory)
            .where(
                PriceHistory.track_id == track_id
            )
            .order_by(
                PriceHistory.checked_at.desc()
            )
        )

        return list(result.scalars().all())

    async def create(
        self,
        track_id: int,
        price: int,
    ) -> None:

        history = PriceHistory(
            track_id=track_id,
            price=price,
        )

        self.session.add(history)