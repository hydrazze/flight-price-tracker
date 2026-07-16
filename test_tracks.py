import asyncio

from app.database.session import async_session_maker
from app.repositories.track import TrackRepository


async def main():

    async with async_session_maker() as session:

        repository = TrackRepository(session)

        tracks = await repository.get_active_tracks()

        for track in tracks:
            print(
                track.origin,
                "->",
                track.destination,
                track.departure_date,
                track.target_price,
            )


asyncio.run(main())