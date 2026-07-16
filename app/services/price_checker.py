from app.repositories.track import TrackRepository
from app.providers.travelpayouts import TravelPayoutsClient


class PriceCheckerService:

    def __init__(
        self,
        repository: TrackRepository,
        client: TravelPayoutsClient,
    ):
        self.repository = repository
        self.client = client


    async def check_prices(self) -> None:

        tracks = await self.repository.get_active_tracks()

        for track in tracks:

            response = await self.client.get_prices_for_dates(
                origin=track.origin,
                destination=track.destination,
                departure_date=track.departure_date,
            )

            if not response.data:
                continue


            cheapest_price = min(
                flight.price
                for flight in response.data
            )


            print(
                f"{track.origin} -> {track.destination}: "
                f"{cheapest_price} руб."
            )


            await self.repository.update_last_price(
                track,
                cheapest_price,
            )