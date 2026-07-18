from app.models.price_history import PriceHistory

from sqlalchemy.ext.asyncio import AsyncSession


class PriceHistoryRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session


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